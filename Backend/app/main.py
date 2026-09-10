import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

def get_application() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
    )

    allow_origins = settings.CORS_ORIGINS
    # Only allow wildcard in explicit development environment. 
    # Do not default to wildcard in production if origins aren't provided.
    if settings.APP_ENV == "development" and "*" not in allow_origins:
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

    from app.websocket.endpoints import router as ws_router
    application.include_router(ws_router, prefix="/ws")

    return application

app = get_application()

@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    return {
        "status": "ok",
        "message": f"{settings.APP_NAME} backend is running!",
        "environment": settings.APP_ENV,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
