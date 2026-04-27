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


settings = Settings()
