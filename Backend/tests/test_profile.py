import pytest
from app.schemas.profile import ProfileUpdate, ContextPreferences
from pydantic import ValidationError

def test_profile_update_schema_valid():
    # Valid data
    update = ProfileUpdate(
        target_role="Backend Developer",
        technologies=["Python", "FastAPI"],
        resume_text="My resume...",
        preferences=ContextPreferences(
            experience_years=5,
            current_company="Tech Corp",
            key_achievements=["Led a team", "Shipped feature X"]
        )
    )
    assert update.target_role == "Backend Developer"
    assert update.technologies == ["Python", "FastAPI"]
    assert update.preferences.experience_years == 5
    assert update.preferences.current_company == "Tech Corp"

def test_profile_update_schema_limits():
    # Test oversized technology list
    with pytest.raises(ValidationError):
        ProfileUpdate(technologies=["Tech"] * 51) # max is 50
        
    # Test oversized target role
    with pytest.raises(ValidationError):
        ProfileUpdate(target_role="A" * 101) # max is 100
        
    # Test oversized preferences
    with pytest.raises(ValidationError):
        ContextPreferences(experience_years=101) # max is 100
        
    with pytest.raises(ValidationError):
        ContextPreferences(key_achievements=["Achieve"] * 21) # max is 20

def test_profile_update_extra_preferences():
    # Test that arbitrary extra context can be placed in preferences
    prefs = ContextPreferences(
        experience_years=2,
        extra_key="some_extra_value"
    )
    assert hasattr(prefs, "extra_key")
    assert prefs.extra_key == "some_extra_value"

# Note: Integration tests requiring a database (e.g. GET /api/profile, 
# PUT /api/profile, authorization checks where User A can't access User B, 
# updated_at triggers, etc.) are excluded from static tests since 
# PostgreSQL is not running in this environment.
