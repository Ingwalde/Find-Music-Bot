import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    BOT_TOKEN: str | None = os.getenv("BOT_TOKEN")
    GENIUS_TOKEN: str | None = os.getenv("GENIUS_TOKEN")

    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/music_bot.db")
    MAX_SEARCH_RESULTS: int = int(os.getenv("MAX_SEARCH_RESULTS", "10"))

    def validate(self) -> None:
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is not set. Add it to your .env file.")

        if self.MAX_SEARCH_RESULTS < 1:
            raise ValueError("MAX_SEARCH_RESULTS must be greater than 0.")

        if self.MAX_SEARCH_RESULTS > 20:
            raise ValueError("MAX_SEARCH_RESULTS should not be greater than 20.")


settings = Settings()
