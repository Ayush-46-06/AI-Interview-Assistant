import pytest
import os
import uuid
import base64
import json
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import WebSocketDisconnect

from app.main import app
from app.models.user import User
from app.models.interview_session import InterviewSession
from app.schemas.session import SessionCreate, AnswerMode
from app.api.dependencies import get_current_user, get_db

client = TestClient(app)

# Dummy objects
dummy_user = User(id=uuid.uuid4(), email="ws@test.com", is_active=True)
dummy_session_id = uuid.uuid4()

@pytest.fixture
def mock_dependencies():
    # Mock get_current_user
    auth_patcher = patch("app.websocket.endpoints.get_current_user", new_callable=AsyncMock)
    mock_auth = auth_patcher.start()
    mock_auth.return_value = dummy_user
    
    def check_token(*args, **kwargs):
        if kwargs.get('token') != 'valid_token' and kwargs.get('token') != 'valid':
            raise Exception("Invalid token")
        return dummy_user
    mock_auth.side_effect = check_token

    # Mock DB Query for session ownership
    execute_patcher = patch("app.websocket.endpoints.AsyncSession.execute", new_callable=AsyncMock)
    mock_execute = execute_patcher.start()
    mock_result = MagicMock()
    mock_session = InterviewSession(id=dummy_session_id, user_id=dummy_user.id)
    mock_result.scalars().first.return_value = mock_session
    mock_execute.return_value = mock_result

    # Mock STT
    stt_patcher = patch("app.websocket.endpoints.transcribe_audio", new_callable=AsyncMock)
    mock_stt = stt_patcher.start()
    mock_stt.return_value = "This is a transcribed question."
    
    # Mock AI Stream
    ai_patcher = patch("app.websocket.endpoints.stream_interview_answer")
    mock_ai = ai_patcher.start()
    async def mock_stream(*args, **kwargs):
        yield {"type": "chunk", "content": "This "}
        yield {"type": "chunk", "content": "is "}
        yield {"type": "chunk", "content": "an answer."}
        yield {"type": "meta", "latency_ms": 100, "token_usage": {"total_tokens": 10}, "model": "test-model"}
    mock_ai.side_effect = mock_stream
    
    # Mock Follow-up suggestions
    sug_patcher = patch("app.websocket.endpoints.generate_followup_suggestions", new_callable=AsyncMock)
    mock_sug = sug_patcher.start()
    mock_sug.return_value = ["Could you explain further?", "What was the result?"]

    # Mock persistence
    patch("app.websocket.endpoints.create_question", new_callable=AsyncMock, return_value=MagicMock(id=uuid.uuid4())).start()
    patch("app.websocket.endpoints.create_answer", new_callable=AsyncMock).start()
    
    mock_ended = MagicMock()
    mock_ended.question_count = 1
    mock_ended.ended_at.isoformat.return_value = "2023-01-01T00:00:00"
    mock_ended.score = 85.0
    patch("app.websocket.endpoints.end_session", new_callable=AsyncMock, return_value=mock_ended).start()

    yield
    
    app.dependency_overrides.clear()
    patch.stopall()

def test_ws_invalid_token():
    session_id = uuid.uuid4()
    with client.websocket_connect(f"/ws/interview/{session_id}?token=invalid_token") as websocket:
        resp = websocket.receive_json()
        assert resp["event"] == "error"
        with pytest.raises(WebSocketDisconnect) as exc_info:
            websocket.receive_json()
        assert exc_info.value.code == 1008

def test_ws_unauthorized_session(mock_dependencies):
    # If the session doesn't belong to the user, the DB mock needs to return None
    with patch("app.websocket.endpoints.AsyncSession.execute", new_callable=AsyncMock) as m_exec:
        m_result = MagicMock()
        m_result.scalars().first.return_value = None
        m_exec.return_value = m_result
        
        with client.websocket_connect(f"/ws/interview/{dummy_session_id}?token=valid_token") as websocket:
            resp = websocket.receive_json()
            assert resp["event"] == "error"
            with pytest.raises(WebSocketDisconnect) as exc_info:
                websocket.receive_json()
            assert exc_info.value.code == 1008

def test_ws_full_flow(mock_dependencies):
    with client.websocket_connect(f"/ws/interview/{dummy_session_id}?token=valid_token") as websocket:
        # Start recording
        websocket.send_json({"event": "start_recording"})
        resp = websocket.receive_json()
        assert resp["event"] == "recording_started"
        
        # Audio chunk
        dummy_audio = base64.b64encode(b"fake audio data").decode("utf-8")
        websocket.send_json({"event": "audio_chunk", "payload": {"audio": dummy_audio}})
        
        # Stop recording
        websocket.send_json({"event": "stop_recording"})
        resp = websocket.receive_json()
        assert resp["event"] == "transcription_complete"
        assert resp["transcript"] == "This is a transcribed question."
        
        resp = websocket.receive_json()
        assert resp["event"] == "question_processed"
        
        # Request answer
        websocket.send_json({"event": "request_answer", "payload": {"mode": "Normal"}})
        
        chunks = []
        for _ in range(3):
            resp = websocket.receive_json()
            if resp["event"] == "error":
                print("SERVER ERROR:", resp)
            assert resp["event"] == "answer_streaming"
            chunks.append(resp["chunk"])
            
        assert "".join(chunks) == "This is an answer."
        
        resp = websocket.receive_json()
        assert resp["event"] == "answer_complete"
        
        resp = websocket.receive_json()
        assert resp["event"] == "followup_suggestions"
        
        # End session
        websocket.send_json({"event": "end_session"})
        resp = websocket.receive_json()
        assert resp["event"] == "session_summary"
        assert resp["summary"]["score"] == 85.0
        
        with pytest.raises(WebSocketDisconnect) as exc_info:
            websocket.receive_json()
        assert exc_info.value.code == 1000

def test_ws_invalid_state_transitions(mock_dependencies):
    with client.websocket_connect(f"/ws/interview/{dummy_session_id}?token=valid_token") as websocket:
        # Audio chunk before start
        websocket.send_json({"event": "audio_chunk", "payload": {"audio": "123"}})
        resp = websocket.receive_json()
        assert resp["event"] == "error"
        assert "Not currently recording" in resp["error"]
        
        # Stop recording before start
        websocket.send_json({"event": "stop_recording"})
        resp = websocket.receive_json()
        assert resp["event"] == "error"
        
        # Request answer before question
        websocket.send_json({"event": "request_answer", "payload": {"mode": "Normal"}})
        resp = websocket.receive_json()
        assert resp["event"] == "error"
        assert "No active question" in resp["error"]

def test_ws_cleanup_after_stt_failure(mock_dependencies):
    with patch("app.websocket.endpoints.transcribe_audio", new_callable=AsyncMock) as m_stt:
        m_stt.side_effect = Exception("STT Failed")
        
        with patch("os.remove") as mock_remove:
            with client.websocket_connect(f"/ws/interview/{dummy_session_id}?token=valid") as websocket:
                websocket.send_json({"event": "start_recording"})
                websocket.receive_json()
                
                dummy_audio = base64.b64encode(b"fake audio").decode("utf-8")
                websocket.send_json({"event": "audio_chunk", "payload": {"audio": dummy_audio}})
                
                websocket.send_json({"event": "stop_recording"})
                resp = websocket.receive_json()
                
                assert resp["event"] == "error"
                assert "Transcription failed" in resp["error"]
                
            assert mock_remove.called, "Temp file must be removed even on STT failure"

def test_ws_audio_size_limit(mock_dependencies, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "WS_MAX_AUDIO_BYTES", 10)
    
    with client.websocket_connect(f"/ws/interview/{dummy_session_id}?token=valid") as websocket:
        websocket.send_json({"event": "start_recording"})
        websocket.receive_json()
        
        # Send 15 bytes, exceeding the 10 byte limit
        dummy_audio = base64.b64encode(b"123456789012345").decode("utf-8")
        websocket.send_json({"event": "audio_chunk", "payload": {"audio": dummy_audio}})
        
        resp = websocket.receive_json()
        assert resp["event"] == "error"
        
        with pytest.raises(WebSocketDisconnect) as exc_info:
            websocket.receive_json()
            
    assert exc_info.value.code == 1009
            
    assert exc_info.value.code == 1009
