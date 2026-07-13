"""
main.py
-------
Application entrypoint.

Why this file exists:
    This is what Uvicorn/Render actually runs. Its job is purely to
    ASSEMBLE the application:
        1. Create the FastAPI instance.
        2. Validate that required secrets exist (fail fast on startup,
           not on the first request).
        3. Configure CORS so your Vercel frontend (and localhost during
           development) is allowed to call this API from the browser.
        4. Mount the routers (currently just chat.py) and the /health
           endpoint.

    No business logic lives here — that belongs in services/ and
    routers/. This keeps main.py short and easy to scan.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models import HealthResponse
from app.routers import chat

settings = get_settings()

# Fail fast: if GEMINI_API_KEY (or another required secret) is missing,
# raise a clear error the moment the app starts, instead of letting the
# server boot successfully and only failing on the first /chat request.
settings.validate_required_secrets()

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API powering the AI Clinic Assistant.",
    version="1.0.0",
)

# --- CORS configuration ---
# Browsers block cross-origin requests by default. Since our frontend
# (Vercel) and backend (Render) live on different domains, we must
# explicitly allow the frontend's origin(s) here, or every request from
# the browser will be silently rejected by CORS policy.
#
# allowed_origins_list comes from the ALLOWED_ORIGINS env var in config.py
# — update that env var (not this code) when you add/change your Vercel
# domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
# Mounts all endpoints defined in routers/chat.py (currently POST /chat)
# onto the main app.
app.include_router(chat.router)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """
    Simple liveness check.

    Used by:
    - You, to manually verify the deployment is up.
    - Render's health check system (optional, configurable in render.yaml)
      to know whether to keep routing traffic to this instance.
    - Uptime monitors / load balancers in the future.
    """
    return HealthResponse(status="running")
