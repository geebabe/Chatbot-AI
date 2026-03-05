# AI Chat Service

A real-time AI chat service built with **FastAPI**, the **OpenAI Agents SDK**, and **PostgreSQL**. It provides streaming responses via Server-Sent Events (SSE), with persistent chat history scoped per user and per session.

## Architecture

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

## Quick Start

### Prerequisites
- Docker and Docker Compose
- An OpenAI API key

### Run with Docker

```bash
# Set your OpenAI API key
export OPENAI_API_KEY=sk-...

# Build and start
docker compose up --build
```

The service starts at **http://localhost:8000**. Alembic migrations run automatically on startup.

### API Endpoints

| Method   | Path                                 | Description                     |
|----------|--------------------------------------|---------------------------------|
| `POST`   | `/api/v1/chat/stream`                | Stream an AI response via SSE   |
| `GET`    | `/api/v1/sessions/{id}/history`      | Get a session's message history |
| `DELETE` | `/api/v1/sessions/{id}`              | Delete a session and messages   |
| `GET`    | `/api/v1/health`                     | Health check                    |

### Example: Stream a chat message

```bash
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    "user_id": "user-123",
    "message": "What is the capital of France?"
  }'
```

---

## Running Tests

Tests use an in-memory SQLite database and mock the OpenAI agent — no external services needed.

```bash
# Install dependencies (if running locally)
pip install -r requirements.txt

# Run the test suite
pytest test/ -v
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
