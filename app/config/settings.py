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


def parse_bool(value: str | None, default: bool = True) -> bool:
    """
    Parses boolean values from environment variables.
    """
    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    BOT_TOKEN: str | None = os.getenv("BOT_TOKEN")
    GENIUS_TOKEN: str | None = os.getenv("GENIUS_TOKEN") or os.getenv("GENIUS")

    # DATABASE_PATH — migration-only; used by scripts/migrate_sqlite_to_postgres.py.
    # Remove in a later cleanup once migration has run on all environments.
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/music_bot.db")

    DATABASE_URL: str | None = os.getenv("DATABASE_URL")

    MAX_SEARCH_RESULTS: int = int(os.getenv("MAX_SEARCH_RESULTS", "15"))
    RESULTS_PER_PAGE: int = int(os.getenv("RESULTS_PER_PAGE", "5"))
    HISTORY_LIMIT: int = int(os.getenv("HISTORY_LIMIT", "10"))
    MAX_HISTORY_PER_USER: int = int(os.getenv("MAX_HISTORY_PER_USER", "100"))

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "text").lower()
    LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "logs/bot.log")
    ERROR_HISTORY_LIMIT: int = int(os.getenv("ERROR_HISTORY_LIMIT", "10"))
    ADMIN_ID: int | None = parse_optional_int(os.getenv("ADMIN_ID"))

    SPOTIFY_ENABLED: bool = parse_bool(os.getenv("SPOTIFY_ENABLED"), default=True)
    SPOTIFY_CLIENT_ID: str | None = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET: str | None = os.getenv("SPOTIFY_CLIENT_SECRET")
    SPOTIFY_MARKET: str | None = os.getenv("SPOTIFY_MARKET", "NO")
    SPOTIFY_FORBIDDEN_COOLDOWN_SECONDS: int = int(
        os.getenv("SPOTIFY_FORBIDDEN_COOLDOWN_SECONDS", "3600")
    )

    # Circuit breaker for network-level outages (Spotify/Deezer/Genius) —
    # separate from SPOTIFY_FORBIDDEN_COOLDOWN_SECONDS above, which only
    # covers Spotify's 403 access-restriction case.
    EXTERNAL_SERVICE_COOLDOWN_SECONDS: int = int(
        os.getenv("EXTERNAL_SERVICE_COOLDOWN_SECONDS", "60")
    )

    SHUTDOWN_TIMEOUT_SECONDS: int = int(os.getenv("SHUTDOWN_TIMEOUT_SECONDS", "30"))

    RATE_LIMIT_MAX_REQUESTS: int = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "20"))
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

    # Webhook mode (v3.3.0+) — polling stays the default; only used when BOT_MODE=webhook.
    BOT_MODE: str = os.getenv("BOT_MODE", "polling")
    WEBHOOK_PUBLIC_URL: str | None = os.getenv("WEBHOOK_PUBLIC_URL")
    WEBHOOK_SECRET_PATH: str | None = os.getenv("WEBHOOK_SECRET_PATH")
    WEBHOOK_SECRET_TOKEN: str | None = os.getenv("WEBHOOK_SECRET_TOKEN")
    WEBHOOK_CERT_PATH: str | None = os.getenv("WEBHOOK_CERT_PATH")
    WEBHOOK_KEY_PATH: str | None = os.getenv("WEBHOOK_KEY_PATH")
    WEBHOOK_PORT: int = int(os.getenv("WEBHOOK_PORT", "8443"))

    @property
    def webhook_enabled(self) -> bool:
        """
        True only when BOT_MODE is explicitly set to "webhook". Any other
        value (including unset) keeps the default polling behavior.
        """
        return self.BOT_MODE == "webhook"

    @property
    def spotify_enabled(self) -> bool:
        """
        Spotify integration is enabled only when explicitly enabled and credentials are set.
        """
        return bool(
            self.SPOTIFY_ENABLED
            and self.SPOTIFY_CLIENT_ID
            and self.SPOTIFY_CLIENT_SECRET
        )

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

        if self.LOG_FORMAT not in {"text", "json"}:
            raise ValueError("LOG_FORMAT must be 'text' or 'json'.")

        if self.ERROR_HISTORY_LIMIT < 1:
            raise ValueError("ERROR_HISTORY_LIMIT must be greater than 0.")

        if self.ERROR_HISTORY_LIMIT > 50:
            raise ValueError("ERROR_HISTORY_LIMIT should not be greater than 50.")

        if self.SPOTIFY_FORBIDDEN_COOLDOWN_SECONDS < 60:
            raise ValueError("SPOTIFY_FORBIDDEN_COOLDOWN_SECONDS should be at least 60.")

        if self.EXTERNAL_SERVICE_COOLDOWN_SECONDS < 60:
            raise ValueError("EXTERNAL_SERVICE_COOLDOWN_SECONDS should be at least 60.")

        if not self.DATABASE_URL:
            raise ValueError(
                "DATABASE_URL is not set. Add it to your .env file. "
                "Example: DATABASE_URL=postgresql://user:pass@localhost:5432/dbname"
            )

        if self.BOT_MODE not in {"polling", "webhook"}:
            raise ValueError("BOT_MODE must be 'polling' or 'webhook'.")

        if self.webhook_enabled:
            required = {
                "WEBHOOK_PUBLIC_URL": self.WEBHOOK_PUBLIC_URL,
                "WEBHOOK_SECRET_PATH": self.WEBHOOK_SECRET_PATH,
                "WEBHOOK_SECRET_TOKEN": self.WEBHOOK_SECRET_TOKEN,
                "WEBHOOK_CERT_PATH": self.WEBHOOK_CERT_PATH,
                "WEBHOOK_KEY_PATH": self.WEBHOOK_KEY_PATH,
            }
            missing = [name for name, value in required.items() if not value]

            if missing:
                raise ValueError(
                    "BOT_MODE=webhook requires: " + ", ".join(missing)
                )


settings = Settings()
