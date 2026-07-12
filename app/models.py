"""
models.py
---------
Pydantic data models (schemas) shared across the application.

Why this file exists:
    FastAPI uses Pydantic models to:
    1. Validate incoming request bodies automatically (reject bad input
       before it ever reaches our business logic).
    2. Serialize outgoing responses into consistent, documented JSON.
    3. Auto-generate the OpenAPI/Swagger docs at /docs.

    Keeping all schemas in a single models.py (rather than defining them
    inline inside routers) means:
    - One source of truth for the shape of our data.
    - Routers and services can import the same class, so there's no
      mismatch between what's validated and what's returned.
    - Easy to extend later (e.g. adding conversation_id, user_id, etc.)
      without touching router logic.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """
    Schema for incoming POST /chat requests.

    Example request body:
        {
            "message": "What are your clinic's opening hours?"
        }
    """

    message: str = Field(
        ...,  # "..." means this field is required
        min_length=1,
        max_length=2000,
        description="The user's message to the clinic assistant.",
        examples=["What are your opening hours?"],
    )


class ChatResponse(BaseModel):
    """
    Schema for outgoing POST /chat responses.

    Example response body:
        {
            "reply": "Our clinic is open Monday to Saturday, 9am - 6pm."
        }
    """

    reply: str = Field(
        ...,
        description="The AI assistant's generated reply.",
    )


class HealthResponse(BaseModel):
    """
    Schema for GET /health responses.

    Example response body:
        {
            "status": "running"
        }
    """

    status: str = Field(
        default="running",
        description="Indicates the API is up and responding.",
    )
