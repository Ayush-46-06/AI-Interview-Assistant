import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app
from app.models.user import User

client = TestClient(app)
dummy_user = User(id=uuid4(), email="wt@test.com", is_active=True)

@pytest.fixture
def mock_auth():
    with patch("app.api.v1.endpoints.weak_topics.get_current_user", new_callable=AsyncMock) as m_auth:
        m_auth.return_value = dummy_user
        yield m_auth

def test_weak_topics_authenticated_access(mock_auth):
    from app.api.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    with patch("app.services.weak_topic.AsyncSession.execute", new_callable=AsyncMock) as m_exec:
        m_result = MagicMock()
        m_result.scalars().all.return_value = [
            MagicMock(id=uuid4(), user_id=dummy_user.id, topic="python", category="python", frequency=2, avg_score=40.0, last_encountered=datetime.utcnow())
        ]
        m_exec.return_value = m_result
        
        response = client.get("/api/weak-topics/", headers={"Authorization": "Bearer token"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["topic"] == "python"
        assert data[0]["frequency"] == 2
        
    app.dependency_overrides.clear()

@pytest.mark.anyio
async def test_weak_topic_update_logic():
    from app.services.feedback import update_weak_topics_on_feedback
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    
    # Test creation
    m_topic_result = MagicMock()
    m_topic_result.scalars().first.return_value = None
    mock_db.execute.return_value = m_topic_result
    
    await update_weak_topics_on_feedback(mock_db, dummy_user.id, "python", 2) # Rating 2 -> 40 score
    mock_db.add.assert_called_once()
    added_topic = mock_db.add.call_args[0][0]
    assert added_topic.topic == "python"
    assert added_topic.frequency == 1
    assert added_topic.avg_score == 40.0
    
    # Test update existing
    mock_db.reset_mock()
    existing_topic = MagicMock(frequency=1, avg_score=40.0)
    m_topic_result.scalars().first.return_value = existing_topic
    
    await update_weak_topics_on_feedback(mock_db, dummy_user.id, "python", 1) # Rating 1 -> 20 score
    # average of 40 and 20 is 30. Frequency becomes 2.
    assert existing_topic.frequency == 2
    assert existing_topic.avg_score == 30.0
