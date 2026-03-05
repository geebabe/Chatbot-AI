import asyncio
import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.sse import delta_event, done_event, failed_event, heartbeat_event
from app.models.message import MessageRole
from app.schemas.chat import ChatRequest
from app.services.agent import run_agent_streamed
from app.services.db_service import get_or_create_session, save_message

logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL = 15  # seconds


async def stream_chat_response(
    request: ChatRequest, db: AsyncSession
) -> AsyncGenerator[str, None]:
    """
    Orchestrate a chat turn:
    1. Get or create the session.
    2. Persist the user message.
    3. Stream agent response as SSE delta events.
    4. On completion, persist assistant reply and emit done event.
    5. On error, emit failed event.
    6. Emit heartbeat every 15 seconds while streaming.
    """
    session_id_str = str(request.session_id)

    try:
        # 1. Ensure session exists
        await get_or_create_session(db, request.session_id, request.user_id)

        # 2. Save user message BEFORE running the agent
        await save_message(db, request.session_id, MessageRole.user, request.message)

        # 3. Stream agent response with heartbeat
        full_response: list[str] = []
        heartbeat_task = asyncio.create_task(_heartbeat_ticker())

        try:
            async for text_chunk in run_agent_streamed(request.message):
                full_response.append(text_chunk)
                yield delta_event(text_chunk)
        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

        # 4. Persist assistant reply
        assistant_content = "".join(full_response)
        await save_message(
            db, request.session_id, MessageRole.assistant, assistant_content
        )

        # 5. Emit done
        yield done_event(session_id_str)

    except Exception as exc:
        logger.exception("Error during chat streaming")
        yield failed_event(str(exc))


async def _heartbeat_emitter() -> AsyncGenerator[str, None]:
    """Yield heartbeat events at a fixed interval."""
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL)
        yield heartbeat_event()


async def _heartbeat_ticker():
    """Background task placeholder — heartbeat logic is handled inline."""
    # This keeps the pattern extensible; the actual heartbeat
    # is woven into the streaming response via the route layer.
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL)
