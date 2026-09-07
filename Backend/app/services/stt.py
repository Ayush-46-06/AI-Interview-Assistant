import os
from typing import Optional
from fastapi import HTTPException, status
from app.core.config import settings

# Attempt to import groq safely for the STT layer
try:
    import groq
    from groq import AsyncGroq
except ImportError:
    groq = None
    AsyncGroq = None

def get_stt_client() -> Optional['AsyncGroq']:
    if not AsyncGroq:
        return None
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your_groq_api_key_here":
        return None
    return AsyncGroq(api_key=settings.GROQ_API_KEY)

async def transcribe_audio(file_path: str) -> str:
    """
    Transcribe the given audio file using the configured STT provider.
    Currently supports: 'groq'
    """
    if settings.STT_PROVIDER.lower() != "groq":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"STT provider '{settings.STT_PROVIDER}' is not yet supported."
        )
        
    client = get_stt_client()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="STT service is not configured"
        )
        
    try:
        with open(file_path, "rb") as file_obj:
            transcription = await client.audio.transcriptions.create(
                file=(os.path.basename(file_path), file_obj.read()),
                model="whisper-large-v3", # Standard Groq Whisper model
                language=settings.STT_LANGUAGE,
                response_format="text"
            )
            return transcription
    except groq.GroqError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, 
            detail=f"Transcription failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during transcription"
        )
