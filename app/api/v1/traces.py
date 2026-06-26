from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.repositories.memory_repository import MemoryRepository

router = APIRouter(prefix="/api/v1/traces", tags=["Agent Traces"])


class AgentTraceResponse(BaseModel):
    id: int
    agent_name: str
    action: str
    details: str | None
    trace: str | None
    created_at: str

    model_config = {"from_attributes": True}


@router.get(
    "/{user_id}",
    response_model=list[AgentTraceResponse],
    summary="Get agent reasoning traces",
)
def get_traces(
    user_id: int,
    limit: int = Query(default=50, le=100),
    db: Session = Depends(get_db),
) -> list[dict]:
    traces = MemoryRepository(db).list_traces(user_id, limit)
    return [
        {
            "id": t.id,
            "agent_name": t.agent_name,
            "action": t.action,
            "details": t.details,
            "trace": t.trace,
            "created_at": t.created_at.isoformat(),
        }
        for t in traces
    ]
