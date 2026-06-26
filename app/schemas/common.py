from pydantic import BaseModel


class HealthResponse(BaseModel):
    application: str
    version: str
    status: str
    environment: str = "development"
    timestamp: str = ""
    ai_enabled: bool = False
