from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

def get_application() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
    )

    # Allow local frontend development by default, but this should be 
    # configurable for production
    allow_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
    if settings.APP_ENV == "development":
        allow_origins.append("*")

    application.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.api.v1.router import api_router
    application.include_router(api_router, prefix="/api")

    return application

app = get_application()

@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    return {
        "status": "ok",
        "message": f"{settings.APP_NAME} backend is running!",
        "environment": settings.APP_ENV,
    }
