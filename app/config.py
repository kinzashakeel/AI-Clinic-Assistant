"""
config.py
---------
Centralized application configuration.

Why this file exists:
    Every other module in this project (services, routers, main) needs access
    to settings like API keys, the active LLM provider, and CORS origins.
    Instead of scattering `os.getenv(...)` calls throughout the codebase,
    we load and validate everything ONCE here using pydantic-settings.

    Benefits:
    - Type validation: if GEMINI_API_KEY is missing, the app fails fast with
      a clear error instead of crashing later mid-request.
    - Single source of truth: change an env var name in one place.
    - Easy testing: settings can be overridden/mocked in tests.

Environment variables are loaded from a `.env` file in local development
(via python-dotenv, wired in automatically by pydantic-settings) and from
the platform's real environment variables in production (e.g. Render).
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Typed application settings.

    Each attribute maps to an environment variable of the same name
    (case-insensitive). Defaults are provided where safe; secrets
    (like API keys) have no default and MUST be supplied via .env
    or the hosting platform's environment variable settings.
    """

    # --- App metadata ---
    APP_NAME: str = "AI Clinic Assistant Backend"
    APP_ENV: str = "development"  # "development" | "production"

    # --- LLM provider selection ---
    # This is the key to our "swap providers later" requirement.
    # llm_service.py reads this value to decide which provider class to
    # instantiate. To migrate to OpenAI in the future, you would:
    #   1. Add an OpenAIProvider class in llm_service.py
    #   2. Set LLM_PROVIDER=openai in the environment
    # No other file needs to change.
    LLM_PROVIDER: str = "gemini"

    # --- Gemini (Google AI Studio) configuration ---
    GEMINI_API_KEY: str = ""  # required in production, validated below
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # --- CORS configuration ---
    # Comma-separated list of allowed origins, provided via env var so it
    # can differ between local dev and production without code changes.
    # Example: "http://localhost:3000,https://your-app.vercel.app"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Tells pydantic-settings to read a local .env file if present.
    # In production (Render), real environment variables are used instead
    # and this file simply won't exist — that's expected and fine.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def allowed_origins_list(self) -> List[str]:
        """
        Converts the comma-separated ALLOWED_ORIGINS string into a clean
        list of origins, as required by FastAPI's CORSMiddleware.
        """
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    def validate_required_secrets(self) -> None:
        """
        Explicitly checks that critical secrets are present.

        Called once at application startup (see main.py). This is
        intentionally separate from field validation so that the app can
        still be imported (e.g. for testing) without a real API key,
        but will refuse to actually START serving traffic without one.
        """
        if self.LLM_PROVIDER == "gemini" and not self.GEMINI_API_KEY:
            raise RuntimeError(
                "Missing required environment variable: GEMINI_API_KEY. "
                "Set it in your .env file (local) or in your hosting "
                "platform's environment variables (production)."
            )


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.

    Using lru_cache means the .env file / environment is only parsed once
    per process, and every part of the app that calls get_settings() shares
    the exact same Settings object.
    """
    return Settings()
