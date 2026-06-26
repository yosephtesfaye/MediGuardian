from app.services.ai_runner import AIRunner


class CoordinatorService:

    def __init__(self) -> None:
        self.runner = AIRunner()

    async def chat(
        self,
        message: str,
        user_id: str = "1",
        session_id: str = "default",
    ) -> dict:
        return await self.runner.run(
            message=message,
            user_id=user_id,
            session_id=session_id,
        )
