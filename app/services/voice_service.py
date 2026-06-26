import asyncio
import io

from app.core.config import settings
from app.exceptions.errors import AIUnavailableError


class VoiceService:

    async def text_to_speech(self, text: str) -> bytes:
        if not settings.TTS_ENABLED:
            raise AIUnavailableError("Text-to-speech is disabled.")

        try:
            import edge_tts

            communicate = edge_tts.Communicate(text, "en-US-JennyNeural")
            buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buffer.write(chunk["data"])
            return buffer.getvalue()
        except ImportError:
            pass
        except Exception:
            pass

        # Fallback: return empty and let frontend use Web Speech API
        raise AIUnavailableError(
            "TTS unavailable. Use browser speech synthesis on the client."
        )

    def reminder_script(self, medication: str, dosage: str, time: str) -> str:
        return (
            f"Good day. This is MediGuardian reminding you to take "
            f"{medication}, {dosage}, scheduled for {time}."
        )
