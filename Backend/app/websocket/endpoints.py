import os
import uuid
import base64
import json
import asyncio
from typing import Optional, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db, AsyncSessionLocal
from app.core.config import settings
from app.models.user import User
from app.models.interview_session import InterviewSession
from app.api.dependencies import get_current_user
from app.schemas.session import QuestionCreate, AnswerCreate, AnswerMode
from app.services.stt import transcribe_audio
from app.services.session import create_question, create_answer, end_session
from app.services.ai import stream_interview_answer, generate_followup_suggestions

router = APIRouter()

# Dependency to validate JWT from query string
async def get_ws_user(token: str = Query(...), db: AsyncSession = Depends(get_db)) -> User:
    try:
        user = await get_current_user(token=token, db=db)
        return user
    except Exception:
        return None

class InterviewConnection:
    def __init__(self, websocket: WebSocket, session_id: uuid.UUID, user: User, db_session: AsyncSession):
        self.websocket = websocket
        self.session_id = session_id
        self.user = user
        self.db_session = db_session
        
        self.is_recording = False
        self.audio_buffer: bytearray = bytearray()
        self.current_question_id: Optional[uuid.UUID] = None
        self.session_ended = False

    async def send_error(self, message: str):
        await self.websocket.send_json({"event": "error", "error": message})

    async def handle_start_recording(self):
        if self.session_ended:
            return await self.send_error("Session already ended")
        if self.is_recording:
            return await self.send_error("Already recording")
            
        self.is_recording = True
        self.audio_buffer.clear()
        await self.websocket.send_json({"event": "recording_started"})

    async def handle_audio_chunk(self, payload: dict):
        if not self.is_recording:
            return await self.send_error("Not currently recording")
            
        try:
            b64_audio = payload.get("audio", "")
            chunk_bytes = base64.b64decode(b64_audio)
            self.audio_buffer.extend(chunk_bytes)
            
            if len(self.audio_buffer) > settings.WS_MAX_AUDIO_BYTES:
                await self.send_error("Audio buffer size exceeded limit")
                await self.websocket.close(code=1009)
        except Exception:
            await self.send_error("Invalid base64 audio chunk")

    async def handle_stop_recording(self):
        if not self.is_recording:
            return await self.send_error("Not currently recording")
            
        self.is_recording = False
        
        if len(self.audio_buffer) == 0:
            return await self.send_error("No audio recorded")
            
        # Write to temp file
        temp_path = f"/tmp/{uuid.uuid4()}.webm"
        import tempfile
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"{uuid.uuid4()}_ws.webm")
        
        try:
            with open(temp_path, "wb") as f:
                f.write(self.audio_buffer)
                
            self.audio_buffer.clear()
            
            try:
                transcript = await transcribe_audio(temp_path)
            except Exception as e:
                return await self.send_error("Transcription failed")

            await self.websocket.send_json({
                "event": "transcription_complete",
                "transcript": transcript
            })
            
            # Create question
            q_in = QuestionCreate(
                session_id=self.session_id,
                transcript=transcript
            )
            
            try:
                question = await create_question(self.db_session, self.user.id, q_in)
                self.current_question_id = question.id
                await self.websocket.send_json({
                    "event": "question_processed",
                    "question_id": str(question.id),
                    "transcript": transcript
                })
            except Exception as e:
                return await self.send_error("Failed to persist question")
                
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    async def handle_request_answer(self, payload: dict, is_regenerated: bool = False):
        if self.session_ended:
            return await self.send_error("Session already ended")
        if not self.current_question_id:
            return await self.send_error("No active question to answer")
            
        try:
            mode_str = payload.get("mode", "normal")
            try:
                mode = AnswerMode(mode_str)
            except ValueError:
                return await self.send_error("Invalid answer mode")
                
            accumulated_answer = ""
            meta = {}
            
            async for chunk in stream_interview_answer(self.db_session, self.user.id, self.current_question_id, mode):
                if chunk["type"] == "chunk":
                    accumulated_answer += chunk["content"]
                    await self.websocket.send_json({
                        "event": "answer_streaming",
                        "chunk": chunk["content"]
                    })
                elif chunk["type"] == "meta":
                    meta = chunk
                    
            if not accumulated_answer:
                return await self.send_error("AI generation failed or returned empty")
                
            answer_in = AnswerCreate(
                question_id=self.current_question_id,
                answer_text=accumulated_answer,
                model=meta.get("model", "unknown"),
                mode=mode.value,
                latency_ms=meta.get("latency_ms", 0),
                token_usage=meta.get("token_usage", {}),
                is_regenerated=is_regenerated
            )
            
            await create_answer(self.db_session, self.user.id, self.current_question_id, answer_in)
            
            await self.websocket.send_json({
                "event": "answer_complete",
                "answer": accumulated_answer
            })
            
            # Follow-up suggestions
            suggestions = await generate_followup_suggestions(
                self.db_session, self.user.id, self.current_question_id, accumulated_answer
            )
            if suggestions:
                await self.websocket.send_json({
                    "event": "followup_suggestions",
                    "suggestions": suggestions
                })

        except Exception as e:
            return await self.send_error("AI generation error occurred")


    async def handle_end_session(self):
        if self.session_ended:
            return await self.send_error("Session already ended")
            
        try:
            session = await end_session(self.db_session, self.user.id, self.session_id)
            self.session_ended = True
            await self.websocket.send_json({
                "event": "session_summary",
                "summary": {
                    "question_count": session.question_count,
                    "status": "completed" if session.ended_at else "active",
                    "completed_at": session.ended_at.isoformat() if session.ended_at else None,
                    "score": float(session.score) if session.score is not None else None
                }
            })
            await self.websocket.close(code=1000)
        except Exception:
            await self.send_error("Failed to end session")


@router.websocket("/interview/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: uuid.UUID, token: str = Query(...)):
    await websocket.accept()
    
    # Needs a dedicated session for the lifetime of this connection
    async with AsyncSessionLocal() as db:
        user = await get_ws_user(token=token, db=db)
        if not user:
            await websocket.send_json({"event": "error", "error": "Invalid or expired token"})
            return await websocket.close(code=1008)
            
        # Verify Session Ownership
        stmt = select(InterviewSession).where(InterviewSession.id == session_id).where(InterviewSession.user_id == user.id)
        result = await db.execute(stmt)
        session = result.scalars().first()
        
        if not session:
            await websocket.send_json({"event": "error", "error": "Session not found or unauthorized"})
            return await websocket.close(code=1008)
            
        connection = InterviewConnection(websocket, session_id, user, db)
        
        try:
            while True:
                text_data = await websocket.receive_text()
                try:
                    data = json.loads(text_data)
                except json.JSONDecodeError:
                    await connection.send_error("Malformed JSON")
                    continue
                    
                event = data.get("event")
                payload = data.get("payload", {})
                
                if event == "start_recording":
                    await connection.handle_start_recording()
                elif event == "audio_chunk":
                    await connection.handle_audio_chunk(payload)
                elif event == "stop_recording":
                    await connection.handle_stop_recording()
                elif event == "request_answer":
                    await connection.handle_request_answer(payload, is_regenerated=False)
                elif event == "regenerate_answer":
                    await connection.handle_request_answer(payload, is_regenerated=True)
                elif event == "end_session":
                    await connection.handle_end_session()
                    break
                else:
                    await connection.send_error("Unknown event")
                    
        except WebSocketDisconnect:
            pass
        except Exception:
            pass
        finally:
            # Cleanup memory buffers on exit
            connection.audio_buffer.clear()
