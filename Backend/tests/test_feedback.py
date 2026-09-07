import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User

client = TestClient(app)

dummy_user = User(id=uuid4(), email="fb@test.com", is_active=True)
dummy_answer_id = uuid4()
dummy_session_id = uuid4()

@pytest.fixture
def mock_auth():
    with patch("app.api.v1.endpoints.feedback.get_current_user", new_callable=AsyncMock) as m_auth:
        m_auth.return_value = dummy_user
        yield m_auth

@pytest.fixture
def mock_db():
    with patch("app.api.dependencies.get_db") as m_db:
        m_session = AsyncMock()
        m_db.return_value = m_session
        yield m_session

def test_feedback_unauthenticated(mock_db):
    response = client.post("/api/feedback/", json={"answerId": str(dummy_answer_id), "rating": 5})
    assert response.status_code == 401

def test_feedback_invalid_rating(mock_auth, mock_db):
    from app.api.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    # Over 5
    response = client.post("/api/feedback/", json={"answerId": str(dummy_answer_id), "rating": 6}, headers={"Authorization": "Bearer token"})
    assert response.status_code == 422
    # Under 1
    response = client.post("/api/feedback/", json={"answerId": str(dummy_answer_id), "rating": 0}, headers={"Authorization": "Bearer token"})
    assert response.status_code == 422
    app.dependency_overrides.clear()

def test_feedback_missing_answer_or_cross_user(mock_auth):
    from app.api.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    with patch("app.services.feedback.AsyncSession.execute", new_callable=AsyncMock) as m_exec:
        m_result = MagicMock()
        m_result.first.return_value = None  # Not found
        m_exec.return_value = m_result
        
        response = client.post("/api/feedback/", json={"answerId": str(dummy_answer_id), "rating": 5}, headers={"Authorization": "Bearer token"})
        assert response.status_code == 404
    app.dependency_overrides.clear()

def test_feedback_authenticated_creation(mock_auth):
    from app.api.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    with patch("app.services.feedback.AsyncSession.execute", new_callable=AsyncMock) as m_exec:
        m_result = MagicMock()
        mock_answer = MagicMock(id=dummy_answer_id)
        mock_question = MagicMock(category="python")
        m_result.first.return_value = (mock_answer, mock_question)
        
        # Mock weak topic result for the update call
        m_topic_result = MagicMock()
        m_topic_result.scalars().first.return_value = None
        m_exec.side_effect = [m_result, m_topic_result]
        
        with patch("app.services.feedback.AsyncSession.commit", new_callable=AsyncMock):
            async def fake_refresh(obj):
                from datetime import datetime
                obj.id = uuid4()
                obj.created_at = datetime.utcnow()
                return obj
            with patch("app.services.feedback.AsyncSession.refresh", side_effect=fake_refresh):
                response = client.post(
                    "/api/feedback/", 
                    json={"answerId": str(dummy_answer_id), "rating": 4, "notes": "good"}, 
                    headers={"Authorization": "Bearer token"}
                )
                assert response.status_code == 201
                data = response.json()
                assert data["rating"] == 4
                assert data["notes"] == "good"
    app.dependency_overrides.clear()

@pytest.mark.anyio
async def test_session_scoring_logic():
    from app.services.feedback import calculate_session_score
    mock_db = AsyncMock()
    
    # Test: unrated answers excluded, multiple ratings
    m_ratings_result = MagicMock()
    m_ratings_result.scalars().all.return_value = [5, 4] # Ratings 5 and 4
    
    m_session_result = MagicMock()
    mock_session = MagicMock()
    m_session_result.scalars().first.return_value = mock_session
    
    mock_db.execute.side_effect = [m_ratings_result, m_session_result]
    
    await calculate_session_score(mock_db, dummy_session_id)
    # 5 -> 100, 4 -> 80. Average = 90
    assert mock_session.score == 90.0
    mock_db.commit.assert_called_once()
    
    # Test: no feedback keeps score NULL
    mock_db.reset_mock()
    m_ratings_result.scalars().all.return_value = []
    mock_db.execute.side_effect = [m_ratings_result, m_session_result]
    
    await calculate_session_score(mock_db, dummy_session_id)
    assert mock_session.score is None
