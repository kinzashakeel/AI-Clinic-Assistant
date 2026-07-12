"""
services/llm_service.py
------------------------
LLM provider abstraction layer.

Why this file exists:
    We want the rest of the app (specifically routers/chat.py) to be
    completely unaware of WHICH AI provider generates replies. It should
    only know "give me a reply for this message."

    This file implements the Strategy pattern:
    - `LLMProvider` is an abstract base class defining the contract every
      provider must follow: `generate_reply(message) -> str`.
    - `GeminiProvider` is the concrete implementation using Google's
      Gemini API (via the google-generativeai SDK).
    - `get_llm_service()` is a factory that reads settings.LLM_PROVIDER
      and returns the correct provider instance.

    HOW TO ADD A NEW PROVIDER LATER (e.g. OpenAI):
        1. Create a new class, e.g. `OpenAIProvider(LLMProvider)`, in this
           file, implementing `generate_reply()` using the OpenAI SDK.
        2. Add an `elif provider_name == "openai":` branch inside
           `get_llm_service()` below.
        3. Set the environment variable LLM_PROVIDER=openai on Render.
        No changes are needed in chat.py, models.py, or main.py.
"""

from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path

import google.generativeai as genai

from app.config import get_settings

# Path to the system prompt file, resolved relative to this file's location
# so it works correctly regardless of the working directory the app is
# started from (important for Render, which may run uvicorn from a
# different CWD than your local machine).
SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "system_prompt.txt"


def _load_system_prompt() -> str:
    """
    Reads the system prompt text from prompts/system_prompt.txt.

    Keeping the prompt in a plain text file (rather than hardcoded as a
    Python string) means non-engineers can update the assistant's
    persona/behavior without touching any code.
    """
    if not SYSTEM_PROMPT_PATH.exists():
        # Fail with a clear, actionable error rather than a vague crash
        # somewhere deep inside the Gemini SDK.
        raise FileNotFoundError(
            f"System prompt file not found at {SYSTEM_PROMPT_PATH}. "
            "Make sure app/prompts/system_prompt.txt exists."
        )
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()


class LLMProvider(ABC):
    """
    Abstract base class (interface) that every LLM provider must implement.

    Any class that inherits from LLMProvider MUST implement generate_reply,
    or Python will raise a TypeError when trying to instantiate it. This
    guarantees every provider is interchangeable from the caller's
    perspective.
    """

    @abstractmethod
    def generate_reply(self, message: str) -> str:
        """
        Given a user message, return the assistant's text reply.

        Args:
            message: The raw user message string.

        Returns:
            The generated reply as a plain string.
        """
        raise NotImplementedError


class GeminiProvider(LLMProvider):
    """
    LLMProvider implementation backed by Google's Gemini API
    (Google AI Studio).
    """

    def __init__(self) -> None:
        settings = get_settings()

        # Configure the Gemini SDK with our API key. This is done once,
        # when the provider is instantiated (not on every request).
        genai.configure(api_key=settings.GEMINI_API_KEY)

        self._system_prompt = _load_system_prompt()

        # The GenerativeModel object is created once and reused across
        # requests for efficiency. system_instruction primes the model
        # with the clinic assistant's persona and rules on every call,
        # without us having to prepend it to each user message manually.
        self._model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            system_instruction=self._system_prompt,
        )

    def generate_reply(self, message: str) -> str:
        """
        Sends the user's message to Gemini and returns the text reply.

        Raises:
            RuntimeError: if Gemini returns an empty/blocked response,
            so the router can translate this into a clean HTTP error
            instead of leaking a raw SDK exception to the client.
        """
        try:
            response = self._model.generate_content(message)
        except Exception as exc:  # noqa: BLE001 - we deliberately wrap all SDK errors
            raise RuntimeError(f"Gemini API request failed: {exc}") from exc

        reply_text = getattr(response, "text", None)
        if not reply_text:
            # This happens if Gemini blocks the response (e.g. safety
            # filters) or returns no candidates.
            raise RuntimeError(
                "Gemini returned an empty response (it may have been "
                "blocked by safety filters)."
            )

        return reply_text.strip()


@lru_cache
def get_llm_service() -> LLMProvider:
    """
    Factory function that returns the active LLMProvider based on the
    LLM_PROVIDER environment variable.

    Cached with lru_cache so the provider (and its underlying SDK client)
    is instantiated only once per process and reused across all requests,
    rather than being rebuilt on every single chat message.
    """
    settings = get_settings()
    provider_name = settings.LLM_PROVIDER.lower()

    if provider_name == "gemini":
        return GeminiProvider()

    # --- Future providers go here ---
    # elif provider_name == "openai":
    #     return OpenAIProvider()

    raise ValueError(
        f"Unsupported LLM_PROVIDER: '{provider_name}'. "
        "Supported values: 'gemini'."
    )
