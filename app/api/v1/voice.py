from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_voice_service
from app.services.voice_service import VoiceService

router = APIRouter(prefix="/api/v1/voice", tags=["Voice"])


@router.get("/speak", summary="Text-to-speech for reminders")
async def speak(
    text: str = Query(..., min_length=1, max_length=500),
    service: VoiceService = Depends(get_voice_service),
) -> Response:
    try:
        audio = await service.text_to_speech(text)
        return Response(content=audio, media_type="audio/mpeg")
    except Exception:
        return Response(
            content=b"",
            status_code=503,
            headers={"X-TTS-Fallback": "browser"},
        )
