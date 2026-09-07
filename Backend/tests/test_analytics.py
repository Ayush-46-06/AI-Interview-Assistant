import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User

client = TestClient(app)
dummy_user = User(id=uuid4(), email="analytics@test.com", is_active=True)

@pytest.fixture
def mock_auth():
    with patch("app.api.v1.endpoints.analytics.get_current_user", new_callable=AsyncMock) as m_auth:
        m_auth.return_value = dummy_user
        yield m_auth

def test_analytics_invalid_timerange(mock_auth):
    from app.api.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    response = client.get("/api/analytics/?timeRange=invalid", headers={"Authorization": "Bearer token"})
    assert response.status_code == 400
    assert "Invalid timeRange" in response.json()["detail"]
    app.dependency_overrides.clear()

def test_analytics_authenticated_access(mock_auth):
    from app.api.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    with patch("app.services.analytics.AsyncSession.execute", new_callable=AsyncMock) as m_exec:
        m_result1 = MagicMock(); m_result1.scalar.return_value = 10
        m_result2 = MagicMock(); m_result2.scalar.return_value = 5
        m_result3 = MagicMock(); m_result3.scalar.return_value = 85.0
        m_result4 = MagicMock(); m_result4.scalar.return_value = 50
        m_result5 = MagicMock(); m_result5.scalar.return_value = 45
        m_result6 = MagicMock(); m_result6.scalar.return_value = 4.2
        m_exec.side_effect = [m_result1, m_result2, m_result3, m_result4, m_result5, m_result6]
        
        response = client.get("/api/analytics/?timeRange=7d&filter=completed", headers={"Authorization": "Bearer token"})
        assert response.status_code == 200
        data = response.json()
        assert data["total_sessions"] == 10
        assert data["completed_sessions"] == 5
        assert data["average_score"] == 85.0
        assert data["total_questions"] == 50
        assert data["answered_questions"] == 45
        assert data["average_rating"] == 4.2
        
    app.dependency_overrides.clear()
