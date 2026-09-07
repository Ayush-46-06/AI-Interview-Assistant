import os
import uuid
import aiofiles
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.session import (
    QuestionCreate, QuestionResponse, QuestionUpdate,
    AnswerCreate, AnswerResponse, AnswerGenerateRequest
)
from app.services.session import (
    create_question, create_answer, update_question
)
from app.services.ai import generate_interview_answer
from app.services.stt import transcribe_audio

router = APIRouter()

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB
ALLOWED_MIME_TYPES = ["audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav", "audio/ogg", "audio/webm", "video/webm", "audio/mp4"]

@router.post("", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def add_question(
    audio: UploadFile = File(...),
    sessionId: UUID = Form(...),
    category: Optional[str] = Form(None),
    difficulty: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Process uploaded audio, generate a transcript via STT, and create a Question record.
    """
    # 1. Validate Audio
    if not audio.content_type in ALLOWED_MIME_TYPES:
        # Some clients send application/octet-stream for audio, check extension as fallback
        ext = os.path.splitext(audio.filename or "")[1].lower()
        if ext not in [".mp3", ".wav", ".ogg", ".webm", ".m4a"]:
            raise HTTPException(status_code=400, detail="Invalid or unsupported audio format.")
    
    # 2. Safely read and save temp file
    temp_filename = f"/tmp/{uuid.uuid4()}_{audio.filename}"
    # On Windows /tmp/ might not exist reliably, let's use a safe local path or os.path
    import tempfile
    temp_dir = tempfile.gettempdir()
    safe_filename = f"{uuid.uuid4()}_{audio.filename or 'audio.webm'}"
    temp_path = os.path.join(temp_dir, safe_filename)
    
    file_size = 0
    try:
        async with aiofiles.open(temp_path, 'wb') as out_file:
            while chunk := await audio.read(1024 * 1024):  # 1MB chunks
                file_size += len(chunk)
                if file_size > MAX_FILE_SIZE:
                    raise HTTPException(status_code=413, detail="Audio file is too large.")
                await out_file.write(chunk)
                
        if file_size == 0:
            raise HTTPException(status_code=400, detail="Audio file is empty.")
            
        # 3. Process STT
        transcript = await transcribe_audio(temp_path)
        
        # 4. Create Question Persistence
        question_in = QuestionCreate(
            session_id=sessionId,
            transcript=transcript,
            category=category,
            difficulty=difficulty
        )
        # create_question inherently verifies session ownership inside its logic
        return await create_question(db, current_user.id, question_in)
        
    finally:
        # Ensure cleanup of transient audio
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


@router.put("/{question_id}", response_model=QuestionResponse, status_code=status.HTTP_200_OK)
async def modify_question(
    question_id: UUID,
    question_in: QuestionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Allow the user to modify/correct the generated transcript before submitting to AI.
    """
    return await update_question(db, current_user.id, question_id, question_in.transcript)

@router.post("/answer", response_model=AnswerResponse, status_code=status.HTTP_201_CREATED)
async def add_answer(
    generate_req: AnswerGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint for AI Answer generation and persistence.
    """
    answer_in = await generate_interview_answer(
        db=db,
        user_id=current_user.id,
        question_id=generate_req.question_id,
        answer_mode=generate_req.answer_mode
    )
    return await create_answer(db, current_user.id, generate_req.question_id, answer_in)
