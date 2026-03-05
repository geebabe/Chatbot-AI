import asyncio
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.sse import heartbeat_event
from app.db.session import get_db
from app.schemas.chat import ChatRequest
from app.services.chat_service import stream_chat_response

router = APIRouter()


async def _with_heartbeat(
    event_gen: AsyncGenerator[str, None],
) -> AsyncGenerator[str, None]:
    """
    Wrap an SSE event generator with periodic heartbeat events.
    Yields events from the inner generator, interleaved with heartbeat
    events every 15 seconds of inactivity.
    """
    heartbeat_interval = 15
    done = False

    async def _drain():
        nonlocal done
        async for event in event_gen:
            yield event
        done = True

    inner = _drain().__aiter__()

    while not done:
        try:
            event = await asyncio.wait_for(
                inner.__anext__(), timeout=heartbeat_interval
            )
            yield event
        except asyncio.TimeoutError:
            yield heartbeat_event()
        except StopAsyncIteration:
            break


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Accept a user message, run the agent, stream the response via SSE."""
    event_generator = stream_chat_response(request, db)
    return StreamingResponse(
        _with_heartbeat(event_generator),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
