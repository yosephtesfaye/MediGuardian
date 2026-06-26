from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.agents.coordinator.service import CoordinatorService
from app.dependencies import get_coordinator_service
from app.schemas.chat import AgentTrace, ChatRequest, ChatResponse

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "",
    response_model=ChatResponse,
    summary="Chat with MediGuardian AI",
    description="Natural language interface to the multi-agent system.",
)
@limiter.limit("30/minute")
async def chat(
    request: Request,
    payload: ChatRequest,
    service: CoordinatorService = Depends(get_coordinator_service),
) -> ChatResponse:
    result = await service.chat(
        message=payload.message,
        user_id=payload.user_id,
        session_id=payload.session_id,
    )
    return ChatResponse(
        response=result["response"],
        agent=result.get("agent", "Coordinator"),
        traces=[AgentTrace(**t) for t in result.get("traces", [])],
    )
