import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


def parse_optional_int(value: str | None) -> int | None:
    """
    Safely parses optional integer values from environment variables.
    """
    if value is None or value.strip() == "":
        return None

    try:
        return int(value)
    except ValueError:
        return None


@dataclass
class Settings:
    BOT_TOKEN: str | None = os.getenv("BOT_TOKEN")
    GENIUS_TOKEN: str | None = os.getenv("GENIUS_TOKEN") or os.getenv("GENIUS")

    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/music_bot.db")

    MAX_SEARCH_RESULTS: int = int(os.getenv("MAX_SEARCH_RESULTS", "30"))
    RESULTS_PER_PAGE: int = int(os.getenv("RESULTS_PER_PAGE", "5"))
    HISTORY_LIMIT: int = int(os.getenv("HISTORY_LIMIT", "10"))
    MAX_HISTORY_PER_USER: int = int(os.getenv("MAX_HISTORY_PER_USER", "100"))

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "logs/bot.log")
    ERROR_HISTORY_LIMIT: int = int(os.getenv("ERROR_HISTORY_LIMIT", "10"))
    ADMIN_ID: int | None = parse_optional_int(os.getenv("ADMIN_ID"))

    def validate(self) -> None:
        """
        Validates required and numeric configuration values.
        """
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is not set. Add it to your .env file.")

        if self.MAX_SEARCH_RESULTS < 1:
            raise ValueError("MAX_SEARCH_RESULTS must be greater than 0.")

        if self.MAX_SEARCH_RESULTS > 50:
            raise ValueError("MAX_SEARCH_RESULTS should not be greater than 50.")

        if self.RESULTS_PER_PAGE < 1:
            raise ValueError("RESULTS_PER_PAGE must be greater than 0.")

        if self.RESULTS_PER_PAGE > self.MAX_SEARCH_RESULTS:
            raise ValueError("RESULTS_PER_PAGE cannot be greater than MAX_SEARCH_RESULTS.")

        if self.HISTORY_LIMIT < 1:
            raise ValueError("HISTORY_LIMIT must be greater than 0.")

        if self.HISTORY_LIMIT > 30:
            raise ValueError("HISTORY_LIMIT should not be greater than 30.")

        if self.MAX_HISTORY_PER_USER < self.HISTORY_LIMIT:
            raise ValueError("MAX_HISTORY_PER_USER cannot be smaller than HISTORY_LIMIT.")

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
