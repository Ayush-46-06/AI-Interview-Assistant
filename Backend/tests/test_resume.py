from fastapi.testclient import TestClient
import io
import pypdf
import docx
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch, AsyncMock
from app.main import app
from app.models.user import User
from app.api.dependencies import get_current_user
from app.services.ai import build_system_prompt
from datetime import datetime
from app.models.profile import Profile
from app.models.interview_session import InterviewSession
from app.schemas.session import AnswerMode

client = TestClient(app)
dummy_user = User(id=uuid4(), email="test@test.com", is_active=True)

def create_valid_pdf_bytes(text: str = "Test Resume Text") -> bytes:
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> >>\nendobj\n4 0 obj\n<< /Length 53 >>\nstream\nBT /F1 12 Tf 72 712 Td (Mock Resume Text Extracted) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000289 00000 n \ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n393\n%%EOF\n"
    return pdf_content

def create_valid_docx_bytes(text: str = "Mock Resume Text Extracted") -> bytes:
    doc = docx.Document()
    doc.add_paragraph(text)
    f = io.BytesIO()
    doc.save(f)
    return f.getvalue()

def test_upload_resume_unauthenticated():
    app.dependency_overrides = {}
    response = client.post("/api/profile/resume")
    assert response.status_code == 401

def test_upload_resume_valid_pdf():
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    pdf_bytes = create_valid_pdf_bytes()
    files = {"file": ("resume.pdf", pdf_bytes, "application/pdf")}
    
    with patch("app.api.v1.endpoints.profile.get_or_create_profile", new_callable=AsyncMock) as m_get, \
         patch("app.api.v1.endpoints.profile.update_profile", new_callable=AsyncMock) as m_upd:
        
        m_profile = Profile(
            id=uuid4(), 
            user_id=dummy_user.id, 
            technologies=[], 
            preferences={},
            created_at=datetime.utcnow(), 
            updated_at=datetime.utcnow()
        )
        m_get.return_value = m_profile
        m_upd.return_value = m_profile
        
        response = client.post("/api/profile/resume", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "Mock Resume Text Extracted" in m_upd.call_args[0][2].resume_text

def test_upload_resume_valid_docx():
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    docx_bytes = create_valid_docx_bytes()
    files = {"file": ("resume.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    
    with patch("app.api.v1.endpoints.profile.get_or_create_profile", new_callable=AsyncMock) as m_get, \
         patch("app.api.v1.endpoints.profile.update_profile", new_callable=AsyncMock) as m_upd:
        
        m_profile = Profile(
            id=uuid4(), 
            user_id=dummy_user.id, 
            technologies=[], 
            preferences={},
            created_at=datetime.utcnow(), 
            updated_at=datetime.utcnow()
        )
        m_get.return_value = m_profile
        m_upd.return_value = m_profile
        
        response = client.post("/api/profile/resume", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "Mock Resume Text Extracted" in m_upd.call_args[0][2].resume_text

def test_upload_resume_invalid_extension():
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    docx_bytes = create_valid_docx_bytes()
    files = {"file": ("resume.txt", docx_bytes, "text/plain")}
    
    response = client.post("/api/profile/resume", files=files)
    assert response.status_code == 400
    assert "MIME" in response.json()["detail"] or "extension" in response.json()["detail"]

def test_upload_resume_invalid_mime():
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    pdf_bytes = create_valid_pdf_bytes()
    files = {"file": ("resume.pdf", pdf_bytes, "image/png")}
    
    response = client.post("/api/profile/resume", files=files)
    assert response.status_code == 400
    assert "MIME" in response.json()["detail"]

def test_upload_resume_empty_file():
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    files = {"file": ("resume.pdf", b"", "application/pdf")}
    response = client.post("/api/profile/resume", files=files)
    assert response.status_code == 400
    assert "Empty" in response.json()["detail"]

def test_upload_resume_oversized_file():
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    large_bytes = b"0" * (6 * 1024 * 1024)
    files = {"file": ("resume.pdf", large_bytes, "application/pdf")}
    response = client.post("/api/profile/resume", files=files)
    assert response.status_code == 400
    assert "exceeds" in response.json()["detail"].lower()

def test_upload_resume_malformed_pdf():
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    bad_pdf = b"%PDF-1.4\nThis is not a real PDF"
    files = {"file": ("resume.pdf", bad_pdf, "application/pdf")}
    response = client.post("/api/profile/resume", files=files)
    assert response.status_code == 400
    assert "parse PDF" in response.json()["detail"] or "extract text" in response.json()["detail"] or "image-only" in response.json()["detail"]

def test_upload_resume_malformed_docx():
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    bad_docx = b"PK\x03\x04\nThis is not a real DOCX"
    files = {"file": ("resume.docx", bad_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    response = client.post("/api/profile/resume", files=files)
    assert response.status_code == 400
    assert "parse DOCX" in response.json()["detail"] or "extract text" in response.json()["detail"]

def test_update_context_valid():
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    payload = {
        "target_role": "Backend Engineer",
        "technologies": ["Python", "FastAPI"],
        "jd_text": "Looking for a backend engineer.",
        "preferences": {
            "experience_years": 5,
            "company_info": "Tech Corp",
            "behavioral_context": "Team player",
            "past_projects": ["Project A"],
            "key_achievements": ["Promoted"]
        }
    }
    
    with patch("app.api.v1.endpoints.profile.get_or_create_profile", new_callable=AsyncMock) as m_get, \
         patch("app.api.v1.endpoints.profile.update_profile", new_callable=AsyncMock) as m_upd:
        
        m_profile = Profile(
            id=uuid4(), 
            user_id=dummy_user.id,
            target_role="Backend Engineer",
            technologies=[],
            jd_text="Looking for a backend engineer.",
            preferences={"experience_years": 5, "company_info": "Tech Corp"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        m_get.return_value = m_profile
        m_upd.return_value = m_profile
        
        response = client.post("/api/profile/context", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["target_role"] == "Backend Engineer"
        assert data["jd_text"] == "Looking for a backend engineer."
        assert data["preferences"]["experience_years"] == 5
        assert data["preferences"]["company_info"] == "Tech Corp"

def test_get_profile_returns_context():
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    with patch("app.api.v1.endpoints.profile.get_or_create_profile", new_callable=AsyncMock) as m_get:
        m_profile = Profile(
            id=uuid4(), 
            user_id=dummy_user.id,
            target_role="Test",
            technologies=[],
            jd_text="Test JD",
            resume_text="Test Resume",
            preferences={"experience_years": 1},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        m_get.return_value = m_profile
        response = client.get("/api/profile")
        assert response.status_code == 200
        data = response.json()
        assert "target_role" in data
        assert "jd_text" in data
        assert "preferences" in data
        assert "resume_text" in data

def test_ai_prompt_context_integration():
    profile = Profile(
        target_role="Full Stack",
        technologies=["React", "Node"],
        resume_text="I have 10 years of experience.",
        jd_text="Seeking senior full stack developer.",
        preferences={
            "experience_years": 10,
            "current_company": "Acme",
            "company_info": "Acme is a fast growing startup.",
            "behavioral_context": "I want to show leadership.",
            "past_projects": ["E-commerce app"],
            "key_achievements": ["Increased revenue 20%"]
        }
    )
    
    session = InterviewSession(mode="Technical")
    
    prompt = build_system_prompt(profile, session, AnswerMode.NORMAL)
    
    assert "Target Role: Full Stack" in prompt
    assert "React, Node" in prompt
    assert "Resume Context: I have 10 years of experience." in prompt
    assert "Job Description: Seeking senior full stack developer." in prompt
    assert "Experience Level: 10 years" in prompt
    assert "Current Company: Acme" in prompt
    assert "Company Information: Acme is a fast growing startup." in prompt
    assert "Behavioral Context: I want to show leadership." in prompt
    assert "Past Projects: E-commerce app" in prompt
    assert "Key Achievements: Increased revenue 20%" in prompt
