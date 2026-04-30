import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    BOT_TOKEN: str | None = os.getenv("BOT_TOKEN")
    GENIUS_TOKEN: str | None = os.getenv("GENIUS_TOKEN") or os.getenv("GENIUS")

    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/music_bot.db")

    # Total number of tracks loaded from Deezer for one search.
    MAX_SEARCH_RESULTS: int = int(os.getenv("MAX_SEARCH_RESULTS", "30"))

    # Number of tracks shown on one Telegram page.
    RESULTS_PER_PAGE: int = int(os.getenv("RESULTS_PER_PAGE", "5"))

    # Number of recent unique history items shown to user.
    HISTORY_LIMIT: int = int(os.getenv("HISTORY_LIMIT", "10"))

    # Logging settings.
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "logs/bot.log")

    # Optional admin Telegram ID for admin-only commands like /errors.
    ADMIN_ID: int | None = (
        int(os.getenv("ADMIN_ID"))
        if os.getenv("ADMIN_ID") and os.getenv("ADMIN_ID", "").isdigit()
        else None
    )

    # Number of recent errors shown with /errors.
    ERROR_HISTORY_LIMIT: int = int(os.getenv("ERROR_HISTORY_LIMIT", "10"))

    def validate(self) -> None:
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is not set. Add it to your .env file.")

        if self.MAX_SEARCH_RESULTS < 1:
            raise ValueError("MAX_SEARCH_RESULTS must be greater than 0.")

        if self.MAX_SEARCH_RESULTS > 50:
            raise ValueError("MAX_SEARCH_RESULTS should not be greater than 50.")

        if self.RESULTS_PER_PAGE < 1:
            raise ValueError("RESULTS_PER_PAGE must be greater than 0.")

        if self.RESULTS_PER_PAGE > 10:
            raise ValueError("RESULTS_PER_PAGE should not be greater than 10.")

        if self.HISTORY_LIMIT < 1:
            raise ValueError("HISTORY_LIMIT must be greater than 0.")

        if self.HISTORY_LIMIT > 30:
            raise ValueError("HISTORY_LIMIT should not be greater than 30.")

        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

        if self.LOG_LEVEL not in valid_log_levels:
            raise ValueError(
                "LOG_LEVEL must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL."
            )

        if self.ERROR_HISTORY_LIMIT < 1:
            raise ValueError("ERROR_HISTORY_LIMIT must be greater than 0.")

        if self.ERROR_HISTORY_LIMIT > 50:
            raise ValueError("ERROR_HISTORY_LIMIT should not be greater than 50.")


settings = Settings()
