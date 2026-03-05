from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import chat, health, sessions
from app.db.init_db import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — init DB on startup, dispose on shutdown."""
    await init_db()
    yield
    await close_db()


app = FastAPI(title="AI Chat Service", lifespan=lifespan)

app.include_router(chat.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")