# AI Clinic Assistant — Backend

Production-ready FastAPI backend powering an AI clinic assistant, built on
Google Gemini (Google AI Studio). Designed to be deployed on Render and
consumed by a separate frontend hosted on Vercel.

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app entrypoint (CORS, routers, /health)
│   ├── config.py                # Centralized environment/settings loader
│   ├── models.py                # Pydantic request/response schemas
│   ├── routers/
│   │   └── chat.py              # POST /chat endpoint
│   ├── services/
│   │   └── llm_service.py       # LLM provider abstraction (Gemini today, swappable later)
│   ├── prompts/
│   │   └── system_prompt.txt    # AI assistant persona & rules
│   └── knowledge/
│       ├── clinic_info.md       # Clinic details (placeholder — edit with real info)
│       └── faq.md               # FAQ content (placeholder — edit with real info)
├── requirements.txt
├── render.yaml
├── .env.example
└── README.md
```

## Endpoints

| Method | Path      | Description                          |
|--------|-----------|---------------------------------------|
| GET    | `/health` | Liveness check → `{"status":"running"}` |
| POST   | `/chat`   | Send a message, get an AI reply       |
| GET    | `/docs`   | Interactive Swagger API docs (auto-generated) |

### Example: POST /chat

Request:
```json
{ "message": "What are your opening hours?" }
```

Response:
```json
{ "reply": "Our clinic is open Monday to Saturday, 9am - 6pm." }
```

## Local Setup

1. **Clone the repo and enter the backend folder**
   ```bash
   git clone <your-repo-url>
   cd backend
   ```

2. **Create a virtual environment**
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and add your real `GEMINI_API_KEY` (get one at
   https://aistudio.google.com/app/apikey).

5. **Run the server**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Test it**
   - Open http://127.0.0.1:8000/health in your browser → `{"status":"running"}`
   - Open http://127.0.0.1:8000/docs for interactive API docs

## Deploying to Render

See the accompanying deployment walkthrough. In short:
1. Push this repo to GitHub.
2. Create a new Web Service on Render, connect the repo.
3. Render auto-detects `render.yaml` for build/start commands and Python version.
4. Manually set `GEMINI_API_KEY` in Render's Environment Variables tab (never committed to Git).
5. Set `ALLOWED_ORIGINS` to include your live Vercel frontend URL.
6. Deploy, then verify `/health` and `/docs` on your `*.onrender.com` URL.

## Switching LLM Providers Later

The entire Gemini integration is isolated inside `app/services/llm_service.py`.
To add a new provider (e.g. OpenAI):
1. Add a new class implementing the `LLMProvider` interface in that file.
2. Register it in the `get_llm_service()` factory function.
3. Set `LLM_PROVIDER=<new_provider_name>` in your environment.

No other file in the codebase needs to change.

## Security Notes

- `.env` is git-ignored and must never be committed.
- `GEMINI_API_KEY` is only ever read from environment variables — never hardcoded.
- CORS is restricted to explicitly allowed origins via `ALLOWED_ORIGINS`, not left open to `*`.
