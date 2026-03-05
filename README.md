# AI Chat Service

A real-time AI chat service built with **FastAPI**, the **OpenAI Agents SDK**, and **PostgreSQL**. This project provides a robust implementation of streaming AI responses with persistent chat history.

## Architecture & Design Choices

```
┌──────────┐     SSE Stream      ┌──────────────┐    Streaming     ┌──────────┐
│  Client   │ ◄──────────────── │  FastAPI App  │ ◄───────────── │  OpenAI  │
│           │ ──── POST ──────► │              │ ────────────── │  Agent   │
└──────────┘                    └──────┬───────┘                └──────────┘
                                       │
                                       │ async SQLAlchemy
                                       ▼
                                ┌──────────────┐
                                │  PostgreSQL   │
                                └──────────────┘
```

**Key design decisions:**

- **Streaming-first**: The chat endpoint uses SSE with interleaved heartbeat events (every 15 s) so the connection stays alive and clients get incremental responses token-by-token. This is critical for perceived latency.
- **Persistence order**: The user message is persisted *before* the agent runs, and the assistant reply is persisted *after* streaming completes. This guarantees that every user input is recorded even if the agent fails mid-stream.
- **User scoping**: All database queries filter by both `session_id` and `user_id`, so one user cannot access another's sessions — a simple but effective authorization boundary without middleware.
- **Test isolation**: Tests use an in-memory SQLite database and mock the OpenAI agent, so the full test suite runs in under a second with zero external dependencies.

**Trade-offs:**

- `user_id` is passed as a plain string in the request body rather than being extracted from an auth token. This keeps the scope focused but would need auth middleware in production.
- The heartbeat is implemented at the route level with `asyncio.wait_for` timeout interleaving, which is simple and correct for single-stream use but would need refinement for very high concurrency.

---

## Quick Start (Docker)

The fastest way to get started is using Docker Compose.

1. **Set your OpenAI API key**:
   ```bash
   export OPENAI_API_KEY=sk-...
   ```

2. **Build and start**:
   ```bash
   docker compose up --build
   ```
   The service will be available at **http://localhost:8000**. Database migrations are handled automatically.

---

## Local Development Setup

If you prefer to run the components manually, follow these steps:

### 1. Environment Setup
Clone the repository and create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Backend (FastAPI)
We recommend using a virtual environment:
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the backend
uvicorn app.main:app --reload
```
The API documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 3. Frontend (Streamlit)
The project includes a built-in Streamlit UI for testing the chat interface. Run it in a separate terminal:
```bash
# Make sure your virtual environment is active
streamlit run streamlit_app.py
```
The UI will open automatically at **http://localhost:8501**.

---

## Running Tests

Our test suite is designed for speed and reliability, requiring no external dependencies.

```bash
# Ensure dependencies are installed
pip install -r requirements.txt

# Run all tests
pytest test/ -v
```

---

## API Reference

| Method   | Path                                 | Description                     |
|----------|--------------------------------------|---------------------------------|
| `POST`   | `/api/v1/chat/stream`                | Stream an AI response via SSE   |
| `GET`    | `/api/v1/sessions/{id}/history`      | Get a session's message history |
| `DELETE` | `/api/v1/sessions/{id}`              | Delete a session and messages   |
| `GET`    | `/api/v1/health`                     | Health check                    |

### Example Request
```bash
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    "user_id": "user-123",
    "message": "Hello!"
  }'
```

---

## Project Structure

```
├── app/
│   ├── main.py                # FastAPI application + lifespan
│   ├── api/routes/
│   │   ├── chat.py            # POST /chat/stream (SSE)
│   │   ├── sessions.py        # GET history, DELETE session
│   │   └── health.py          # GET /health
│   ├── core/
│   │   ├── config.py          # Pydantic settings
│   │   └── sse.py             # SSE event formatters
│   ├── db/
│   │   ├── base.py            # SQLAlchemy declarative base
│   │   ├── session.py         # Async engine + session factory
│   │   └── init_db.py         # DB lifecycle hooks
│   ├── models/
│   │   ├── session.py         # ChatSession model
│   │   └── message.py         # ChatMessage model + role enum
│   ├── schemas/
│   │   ├── chat.py            # ChatRequest schema
│   │   └── session.py         # Response schemas
│   └── services/
│       ├── agent.py           # OpenAI Agents SDK wrapper
│       ├── chat_service.py    # Streaming orchestrator
│       └── db_service.py      # Async CRUD operations
├── alembic/
│   ├── env.py                 # Async Alembic config
│   └── versions/001_initial.py
├── test/
│   ├── conftest.py            # Shared fixtures
│   ├── test_sse.py            # Unit tests (SSE event order)
│   └── test_chat_integration.py  # Integration tests (DB)
├── docker-compose.yaml
├── Dockerfile
├── requirements.txt
└── alembic.ini
```
