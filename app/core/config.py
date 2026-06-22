from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    """
    Application configuration.
    """

    APP_NAME = os.getenv("APP_NAME", "MediGuardian AI")

    APP_ENV = os.getenv(
        "APP_ENV",
        "development",
    )

    LOG_LEVEL = os.getenv(
        "LOG_LEVEL",
        "INFO",
    )

    GEMINI_API_KEY = os.getenv(
        "GEMINI_API_KEY"
    )

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:///mediguardian.db",
    )

    def validate(self):

            if not self.GEMINI_API_KEY:

                raise ValueError(
                    "GEMINI_API_KEY is missing."
                )
settings = Settings()