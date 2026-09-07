from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
import os
import tempfile
from pathlib import Path
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.profile import ProfileResponse, ProfileUpdate, ContextUpdate
from app.services.profile import get_or_create_profile, update_profile
from app.services.resume import parse_resume_file

router = APIRouter()

@router.get("/", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the authenticated user's profile/context.
    Creates a sensible default profile if one does not exist.
    """
    profile = await get_or_create_profile(db, current_user.id)
    return profile

@router.put("/", response_model=ProfileResponse)
async def update_user_profile(
    profile_in: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the authenticated user's profile/context.
    """
    try:
        profile = await update_profile(db, current_user.id, profile_in)
        return profile
    except Exception as e:
        # Prevent leaking raw database exceptions
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the profile."
        )

@router.post("/context", response_model=ProfileResponse)
async def update_interview_context(
    context_in: ContextUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the authenticated user's interview-specific context.
    """
    try:
        profile = await update_profile(db, current_user.id, context_in)
        return profile
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the context."
        )

MAX_UPLOAD_SIZE = 5 * 1024 * 1024

@router.post("/resume", response_model=ProfileResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and parse a resume file. Updates the user's profile with extracted text.
    """
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename missing")
    
    # MIME validation
    valid_mimes = [
        "application/pdf", 
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    if file.content_type not in valid_mimes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported MIME type")
    
    # Extension validation
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".docx"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file extension")

    # Limit check
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds 5MB limit")
        
    temp_path = None
    try:
        # Create randomized secure temp file
        fd, temp_path = tempfile.mkstemp(suffix=ext)
        with os.fdopen(fd, 'wb') as f:
            f.write(content)
            
        extracted_text = parse_resume_file(Path(temp_path), file.filename)
        
        # Save to profile securely using existing ownership flow
        profile_update = ProfileUpdate(resume_text=extracted_text)
        profile = await update_profile(db, current_user.id, profile_update)
        return profile
    finally:
        # Guarantee cleanup even on extraction failure
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
