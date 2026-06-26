from pydantic import BaseModel, Field


class CollaborationStep(BaseModel):
    from_agent: str = Field(alias="from")
    to_agent: str = Field(alias="to")
    action: str
    reason: str
    result: str

    model_config = {"populate_by_name": True}


class AgentTrace(BaseModel):
    agent: str
    tool: str | None = None
    args: dict | None = None
    collaboration: list[CollaborationStep] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        examples=["Register aspirin 100mg at 8am daily"],
    )
    user_id: str = Field(default="1", examples=["1"])
    session_id: str = Field(default="default", examples=["session-abc"])


class ChatResponse(BaseModel):
    response: str
    agent: str = "Coordinator"
    traces: list[AgentTrace] = Field(default_factory=list)
