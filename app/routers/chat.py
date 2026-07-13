"""
routers/chat.py
----------------
Defines the POST /chat endpoint.

Why this file exists:
    Routers in FastAPI group related endpoints together. This one owns
    everything related to chatting with the AI assistant.

    This file is intentionally "thin" — it does NOT talk to Gemini
    directly. It only:
    1. Validates the incoming request (via ChatRequest, handled
       automatically by FastAPI/Pydantic).
    2. Delegates the actual AI work to the LLM service layer.
    3. Wraps errors into clean HTTP responses.

    Keeping business logic out of routers makes the API layer easy to
    test and easy to reason about — routers describe "what endpoints
    exist", services describe "how the work actually gets done".
"""

from fastapi import APIRouter, HTTPException

from app.models import ChatRequest, ChatResponse
from app.services.llm_service import get_llm_service

# APIRouter lets us define endpoints in this file and "mount" them onto
# the main FastAPI app in main.py, keeping main.py clean and declarative.
router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Accepts a user message and returns the AI assistant's reply.

    Request body:
        {"message": "What are your opening hours?"}

    Response body:
        {"reply": "Our clinic is open Monday to Saturday, 9am - 6pm."}

    Raises:
        HTTPException(502): if the LLM provider fails to generate a reply
            (e.g. Gemini API error, network issue, safety block). We
            return 502 Bad Gateway because the failure originates from
            an upstream service (Gemini), not from our own API.
    """
    llm_service = get_llm_service()

    try:
        reply_text = llm_service.generate_reply(request.message)
    except RuntimeError as exc:
        # Convert internal service errors into a clean HTTP error rather
        # than leaking raw SDK exception details to the frontend.
        raise HTTPException(
            status_code=502,
            detail=f"Failed to generate a response: {exc}",
        ) from exc

    return ChatResponse(reply=reply_text)
