class OCRService:

    PRESCRIPTION_PROMPT = """Analyze this prescription image and extract medication details.
Return ONLY valid JSON with this structure:
{
  "medications": [
    {
      "name": "medication name",
      "dosage": "dosage amount",
      "instructions": "how to take it",
      "time_of_day": "HH:MM suggested time or empty string"
    }
  ],
  "patient_name": "if visible",
  "doctor_name": "if visible",
  "confidence": "high|medium|low"
}
Do not diagnose. Only extract visible prescription information."""

    async def extract_from_image(self, file) -> dict:
        import json
        import re

        from fastapi import UploadFile

        from app.core.config import settings
        from app.exceptions.errors import AIUnavailableError, ValidationError

        if not settings.GEMINI_API_KEY:
            raise AIUnavailableError(
                "GEMINI_API_KEY required for prescription OCR."
            )

        content = await file.read()
        max_bytes = settings.UPLOAD_MAX_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise ValidationError(
                f"File exceeds {settings.UPLOAD_MAX_MB}MB limit."
            )

        if file.content_type and not file.content_type.startswith("image/"):
            raise ValidationError("Only image files are supported.")

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = client.models.generate_content(
                model=settings.GEMINI_VISION_MODEL,
                contents=[
                    types.Part.from_bytes(
                        data=content,
                        mime_type=file.content_type or "image/jpeg",
                    ),
                    self.PRESCRIPTION_PROMPT,
                ],
            )
            text = response.text or "{}"
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {"medications": [], "raw_text": text, "confidence": "low"}
        except json.JSONDecodeError:
            return {"medications": [], "raw_text": text, "confidence": "low"}
        except Exception as exc:
            raise AIUnavailableError(f"OCR failed: {exc}") from exc
