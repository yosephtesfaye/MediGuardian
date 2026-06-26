from sqlalchemy.orm import Session

from app.models.entities import AgentLog, ConversationMemory, LongTermMemory
from app.repositories.base import BaseRepository


class MemoryRepository(BaseRepository):

    def save_message(
        self,
        user_id: int,
        session_id: str,
        role: str,
        content: str,
    ) -> ConversationMemory:
        entry = ConversationMemory(
            user_id=user_id,
            session_id=session_id,
            role=role,
            content=content,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_recent(
        self,
        user_id: int,
        session_id: str,
        limit: int = 20,
    ) -> list[ConversationMemory]:
        return (
            self.db.query(ConversationMemory)
            .filter(
                ConversationMemory.user_id == user_id,
                ConversationMemory.session_id == session_id,
            )
            .order_by(ConversationMemory.created_at.desc())
            .limit(limit)
            .all()
        )

    def save_long_term(
        self,
        user_id: int,
        fact_key: str,
        fact_value: str,
        embedding: str | None = None,
    ) -> LongTermMemory:
        existing = (
            self.db.query(LongTermMemory)
            .filter(
                LongTermMemory.user_id == user_id,
                LongTermMemory.fact_key == fact_key,
            )
            .first()
        )
        if existing:
            existing.fact_value = fact_value
            if embedding:
                existing.embedding = embedding
            self.db.commit()
            self.db.refresh(existing)
            return existing

        entry = LongTermMemory(
            user_id=user_id,
            fact_key=fact_key,
            fact_value=fact_value,
            embedding=embedding,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def list_long_term(self, user_id: int) -> list[LongTermMemory]:
        return (
            self.db.query(LongTermMemory)
            .filter(LongTermMemory.user_id == user_id)
            .all()
        )

    def log_agent(
        self,
        agent_name: str,
        action: str,
        details: str | None = None,
        user_id: int | None = None,
        trace: str | None = None,
    ) -> AgentLog:
        entry = AgentLog(
            user_id=user_id,
            agent_name=agent_name,
            action=action,
            details=details,
            trace=trace,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def list_traces(self, user_id: int, limit: int = 50) -> list[AgentLog]:
        return (
            self.db.query(AgentLog)
            .filter(AgentLog.user_id == user_id)
            .order_by(AgentLog.created_at.desc())
            .limit(limit)
            .all()
        )
