from fastapi import APIRouter
from app.api.v1.endpoints import auth, profile, session, question, feedback, weak_topics, analytics, settings

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(profile.router, prefix="/profile", tags=["User Profile"])
api_router.include_router(session.router, prefix="/sessions", tags=["Interview Sessions"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["Feedback"])
api_router.include_router(weak_topics.router, prefix="/weak-topics", tags=["Weak Topics"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(question.router, prefix="/questions", tags=["questions"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
