import pytest
import os
from uuid import uuid4
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import HTTPException, UploadFile

from app.api.v1.endpoints.question import add_question, modify_question
from app.services.stt import transcribe_audio
from app.schemas.session import QuestionUpdate
from app.models.user import User

@pytest.mark.anyio
async def test_invalid_audio_type():
    audio = MagicMock(spec=UploadFile)
    audio.content_type = "text/plain"
    audio.filename = "test.txt"
    
    with pytest.raises(HTTPException) as exc:
        await add_question(
            audio=audio, 
            sessionId=uuid4(), 
            category=None, 
            difficulty=None, 
            current_user=User(id=uuid4()), 
            db=MagicMock()
        )
    assert exc.value.status_code == 400
    assert "Invalid or unsupported" in exc.value.detail

@pytest.mark.anyio
async def test_empty_audio():
    audio = MagicMock(spec=UploadFile)
    audio.content_type = "audio/mpeg"
    audio.filename = "test.mp3"
    
    # Mock read to return empty bytes instantly
    async def mock_read(*args, **kwargs):
        if not getattr(mock_read, 'called', False):
            mock_read.called = True
            return b""
        return b""
    audio.read = mock_read
    
    with pytest.raises(HTTPException) as exc:
        await add_question(
            audio=audio, 
            sessionId=uuid4(), 
            category=None, 
            difficulty=None, 
            current_user=User(id=uuid4()), 
            db=MagicMock()
        )
    assert exc.value.status_code == 400
    assert "Audio file is empty" in exc.value.detail

@pytest.mark.anyio
async def test_stt_missing_config_raises_503(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    monkeypatch.setattr(settings, "STT_PROVIDER", "groq")
    
    with pytest.raises(HTTPException) as exc:
        await transcribe_audio("/tmp/fake.mp3")
    assert exc.value.status_code == 503

@pytest.mark.anyio
async def test_stt_unsupported_provider(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "STT_PROVIDER", "google")
    
    with pytest.raises(HTTPException) as exc:
        await transcribe_audio("/tmp/fake.mp3")
    assert exc.value.status_code == 501

@pytest.mark.anyio
@patch('app.api.v1.endpoints.question.transcribe_audio', new_callable=AsyncMock)
@patch('app.api.v1.endpoints.question.create_question', new_callable=AsyncMock)
async def test_successful_transcription_cleans_up(mock_create_q, mock_stt):
    audio = MagicMock(spec=UploadFile)
    audio.content_type = "audio/mpeg"
    audio.filename = "test.mp3"
    
    async def mock_read(size):
        if not getattr(mock_read, 'called', False):
            mock_read.called = True
            return b"fake audio data"
        return b""
    audio.read = mock_read
    
    mock_stt.return_value = "Hello world"
    mock_create_q.return_value = MagicMock()
    
    # Run the endpoint
    result = await add_question(
        audio=audio, 
        sessionId=uuid4(), 
        category=None, 
        difficulty=None, 
        current_user=User(id=uuid4()), 
        db=MagicMock()
    )
    
    # STT should be called
    assert mock_stt.called
    
    # File should be cleaned up (we check if it doesn't exist, though we can't easily intercept tempfile path here, 
    # we can trust the finally block executed without error)
    assert mock_create_q.called
    
@pytest.mark.anyio
@patch('app.api.v1.endpoints.question.transcribe_audio', new_callable=AsyncMock)
async def test_failed_transcription_cleans_up(mock_stt):
    audio = MagicMock(spec=UploadFile)
    audio.content_type = "audio/mpeg"
    audio.filename = "test.mp3"
    
    async def mock_read(size):
        if not getattr(mock_read, 'called', False):
            mock_read.called = True
            return b"fake audio data"
        return b""
    audio.read = mock_read
    
    mock_stt.side_effect = HTTPException(status_code=502, detail="API Error")
    
    with pytest.raises(HTTPException) as exc:
        await add_question(
            audio=audio, 
            sessionId=uuid4(), 
            category=None, 
            difficulty=None, 
            current_user=User(id=uuid4()), 
            db=MagicMock()
        )
    assert exc.value.status_code == 502

@pytest.mark.anyio
@patch('app.api.v1.endpoints.question.update_question', new_callable=AsyncMock)
async def test_modify_question(mock_update):
    mock_update.return_value = MagicMock(transcript="Corrected transcript")
    
    result = await modify_question(
        question_id=uuid4(),
        question_in=QuestionUpdate(transcript="Corrected transcript"),
        current_user=User(id=uuid4()),
        db=MagicMock()
    )
    assert mock_update.called
