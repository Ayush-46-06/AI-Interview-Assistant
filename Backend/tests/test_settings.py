import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from unittest.mock import patch, AsyncMock
from app.main import app
from app.models.user import User
from app.api.dependencies import get_current_user
from datetime import datetime
from app.models.setting import Setting

client = TestClient(app)
dummy_user = User(id=uuid4(), email="test@test.com", is_active=True)

def test_update_settings_unauthenticated():
    app.dependency_overrides = {}
    response = client.put("/api/settings", json={})
    assert response.status_code == 401

def test_screen_invisibility_defaults_false():
    # If the user accesses settings logic without passing it in, defaults apply.
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    
    with patch("app.services.setting.get_or_create_settings", new_callable=AsyncMock) as m_get:
        # User has a clean database settings row
        m_setting = Setting(
            id=uuid4(),
            user_id=dummy_user.id,
            screen_invisibility_enabled=False,
            disclaimer_accepted=False,
            other_preferences={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        m_get.return_value = m_setting
        
        # Test updating unrelated setting
        with patch("app.services.setting.AsyncSession.commit", new_callable=AsyncMock), \
             patch("app.services.setting.AsyncSession.refresh", new_callable=AsyncMock):
             
            response = client.put("/api/settings", json={"other_preferences": {"theme": "dark"}})
            assert response.status_code == 200
            data = response.json()
            assert data["screen_invisibility_enabled"] is False

def test_enable_screen_invisibility_without_disclaimer_rejected():
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    
    with patch("app.services.setting.get_or_create_settings", new_callable=AsyncMock) as m_get:
        m_setting = Setting(
            id=uuid4(),
            user_id=dummy_user.id,
            screen_invisibility_enabled=False,
            disclaimer_accepted=False,
            other_preferences={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        m_get.return_value = m_setting
        
        response = client.put("/api/settings", json={"screen_invisibility_enabled": True})
        assert response.status_code == 400
        assert "ethical" in response.json()["detail"].lower()

def test_enable_screen_invisibility_with_disclaimer_accepted():
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    
    with patch("app.services.setting.get_or_create_settings", new_callable=AsyncMock) as m_get:
        m_setting = Setting(
            id=uuid4(),
            user_id=dummy_user.id,
            screen_invisibility_enabled=False,
            disclaimer_accepted=False,
            other_preferences={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        m_get.return_value = m_setting
        
        with patch("app.services.setting.AsyncSession.commit", new_callable=AsyncMock), \
             patch("app.services.setting.AsyncSession.refresh", new_callable=AsyncMock):
            
            response = client.put("/api/settings", json={
                "screen_invisibility_enabled": True, 
                "disclaimer_accepted": True
            })
            assert response.status_code == 200
            data = response.json()
            assert data["screen_invisibility_enabled"] is True
            assert data["disclaimer_accepted"] is True

def test_disable_screen_invisibility_always_allowed():
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    
    with patch("app.services.setting.get_or_create_settings", new_callable=AsyncMock) as m_get:
        # Already enabled somehow (perhaps previously accepted, but say disclaimer is false or true)
        m_setting = Setting(
            id=uuid4(),
            user_id=dummy_user.id,
            screen_invisibility_enabled=True,
            disclaimer_accepted=False,
            other_preferences={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        m_get.return_value = m_setting
        
        with patch("app.services.setting.AsyncSession.commit", new_callable=AsyncMock), \
             patch("app.services.setting.AsyncSession.refresh", new_callable=AsyncMock):
            
            response = client.put("/api/settings", json={"screen_invisibility_enabled": False})
            assert response.status_code == 200
            data = response.json()
            assert data["screen_invisibility_enabled"] is False

def test_partial_settings_update_preserves_values():
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    
    with patch("app.services.setting.get_or_create_settings", new_callable=AsyncMock) as m_get:
        m_setting = Setting(
            id=uuid4(),
            user_id=dummy_user.id,
            screen_invisibility_enabled=False,
            disclaimer_accepted=False,
            other_preferences={"theme": "dark", "notifications": True},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        m_get.return_value = m_setting
        
        with patch("app.services.setting.AsyncSession.commit", new_callable=AsyncMock), \
             patch("app.services.setting.AsyncSession.refresh", new_callable=AsyncMock):
            
            # Update only one preference
            response = client.put("/api/settings", json={
                "other_preferences": {"notifications": False, "new_pref": 123}
            })
            assert response.status_code == 200
            data = response.json()
            assert data["other_preferences"]["theme"] == "dark"
            assert data["other_preferences"]["notifications"] is False
            assert data["other_preferences"]["new_pref"] == 123
