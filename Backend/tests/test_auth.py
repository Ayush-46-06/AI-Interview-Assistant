import pytest
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token
from app.schemas.auth import UserCreate
from pydantic import ValidationError

def test_password_hashing():
    password = "SuperSecretPassword123!"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert password not in hashed
    assert verify_password(password, hashed)
    assert not verify_password("WrongPassword123!", hashed)

def test_jwt_access_token():
    user_id = "test-user-id"
    token = create_access_token(user_id)
    
    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["type"] == "access"
    assert "exp" in payload

def test_jwt_refresh_token():
    user_id = "test-user-id"
    token = create_refresh_token(user_id)
    
    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"
    assert "exp" in payload

def test_user_create_schema_validation():
    # Valid
    user = UserCreate(email="test@example.com", password="password123", name="Test User")
    assert user.email == "test@example.com"
    
    # Invalid email
    with pytest.raises(ValidationError):
        UserCreate(email="not-an-email", password="password123", name="Test")
        
    # Too short password
    with pytest.raises(ValidationError):
        UserCreate(email="test@example.com", password="short", name="Test")

# Note: Integration tests with the FastAPI client and actual PostgreSQL DB 
# (e.g. testing duplicate email rejection, login failures, etc) are typically
# placed here. Because this environment might not have a running PostgreSQL 
# instance, live database tests are separated from static verification.
