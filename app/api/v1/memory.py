from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.repositories.memory_repository import MemoryRepository
from app.services.dashboard_service import MemoryService

router = APIRouter(prefix="/api/v1/memory", tags=["Memory"])
_memory = MemoryService()


@router.get(
    "/{user_id}",
    summary="Inspect long-term memory",
    description="Returns stored facts and the embedding mode used for semantic recall.",
)
def get_memory(user_id: int, db: Session = Depends(get_db)) -> dict:
    repo = MemoryRepository(db)
    facts = repo.list_long_term(user_id)
    return {
        "user_id": user_id,
        "embedding_modes": {
            "primary": "gemini/text-embedding-004 (768-dim)",
            "fallback": "local hash vectors (128-dim, free/offline)",
        },
        "facts_count": len(facts),
        "facts": [
            {
                "key": f.fact_key,
                "value": f.fact_value,
                "has_gemini_embedding": bool(f.embedding),
            }
            for f in facts
        ],
        "retrieval": (
            "Cosine similarity over stored embeddings; "
            "falls back to local vectors when Gemini quota unavailable"
        ),
    }
