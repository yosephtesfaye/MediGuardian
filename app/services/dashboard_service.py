import json

from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.memory_repository import MemoryRepository
from app.services.memory_embeddings import rank_by_similarity, simple_embed
from app.services.adherence_service import AdherenceService, CaregiverService
from app.services.medication_service import MedicationService
from app.services.reminder_service import ReminderService


class MemoryService:

    def save_message(
        self,
        db: Session,
        user_id: int,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        MemoryRepository(db).save_message(user_id, session_id, role, content)
        if role == "user":
            self._extract_and_store_facts(db, user_id, content)

    def get_history(
        self,
        db: Session,
        user_id: int,
        session_id: str,
        limit: int = 20,
    ) -> list:
        return MemoryRepository(db).get_recent(user_id, session_id, limit)

    def get_context(self, db: Session, user_id: int, query: str) -> str:
        repo = MemoryRepository(db)
        facts = repo.list_long_term(user_id)
        if not facts:
            return ""

        # Primary: Gemini text-embedding-004 (semantic, 768-dim)
        if settings.GEMINI_API_KEY:
            query_emb = self._embed_gemini(query)
            if query_emb:
                scored = []
                for fact in facts:
                    if fact.embedding:
                        fact_emb = json.loads(fact.embedding)
                        score = self._cosine(query_emb, fact_emb)
                        scored.append((score, fact))
                scored.sort(key=lambda x: x[0], reverse=True)
                top = [f"{f.fact_key}: {f.fact_value}" for _, f in scored[:5]]
                return "\n".join(top)

        # Fallback: local hash vectors (128-dim, free — works offline)
        query_vec = simple_embed(query)
        items: list[tuple[str, list[float]]] = []
        for fact in facts:
            if fact.embedding:
                try:
                    vec = json.loads(fact.embedding)
                    if len(vec) == 128:
                        items.append((f"{fact.fact_key}: {fact.fact_value}", vec))
                        continue
                except (json.JSONDecodeError, TypeError):
                    pass
            items.append((f"{fact.fact_key}: {fact.fact_value}", simple_embed(fact.fact_value)))

        ranked = rank_by_similarity(query_vec, items, top_k=5)
        return "\n".join(text for _, text in ranked)

    def _extract_and_store_facts(
        self,
        db: Session,
        user_id: int,
        content: str,
    ) -> None:
        lowered = content.lower()
        repo = MemoryRepository(db)
        if "prefer" in lowered or "remind me" in lowered:
            repo.save_long_term(
                user_id, "preference", content, self._embed_json(content)
            )
        if "allergy" in lowered or "allergic" in lowered:
            repo.save_long_term(
                user_id, "allergy", content, self._embed_json(content)
            )

    def _embed_gemini(self, text: str) -> list[float] | None:
        try:
            from google import genai

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            result = client.models.embed_content(
                model="text-embedding-004",
                contents=text,
            )
            return result.embeddings[0].values
        except Exception:
            return None

    def _embed(self, text: str) -> list[float]:
        """Gemini first, then local hash vectors (always returns a vector)."""
        gemini = self._embed_gemini(text) if settings.GEMINI_API_KEY else None
        return gemini if gemini else simple_embed(text)

    def _embed_json(self, text: str) -> str:
        return json.dumps(self._embed(text))

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        from app.services.memory_embeddings import cosine_similarity

        return cosine_similarity(a, b)


class DashboardService:

    def __init__(self) -> None:
        self.medications = MedicationService()
        self.reminders = ReminderService()
        self.adherence = AdherenceService()
        self.caregivers = CaregiverService()

    def get_summary(self, db: Session, user_id: int) -> dict:
        meds = self.medications.list_for_user(db, user_id)
        today = self.reminders.list_today(db, user_id)
        report = self.adherence.report(db, user_id)
        caregivers = self.caregivers.list_for_user(db, user_id)
        heatmap = self.adherence.heatmap(db, user_id)

        return {
            "user_id": user_id,
            "medications_count": len(meds),
            "medications": [
                {"id": m.id, "name": m.name, "dosage": m.dosage}
                for m in meds
            ],
            "today_reminders": today,
            "adherence": report,
            "heatmap": heatmap,
            "caregivers": [
                {
                    "id": c.id,
                    "name": c.name,
                    "email": c.email,
                    "notify_on_miss_count": c.notify_on_miss_count,
                }
                for c in caregivers
            ],
        }
