from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import ChatMessage, MessageRole
from app.models.session import ChatSession


async def get_or_create_session(
    db: AsyncSession, session_id: UUID, user_id: str
) -> ChatSession:
    """Return an existing session or create a new one."""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id, ChatSession.user_id == user_id
        )
    )
    session = result.scalar_one_or_none()

    if session is None:
        session = ChatSession(id=session_id, user_id=user_id)
        db.add(session)
        await db.commit()
        await db.refresh(session)

    return session


async def save_message(
    db: AsyncSession,
    session_id: UUID,
    role: MessageRole,
    content: str,
) -> ChatMessage:
    """Persist a single chat message."""
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def get_session_history(
    db: AsyncSession, session_id: UUID, user_id: str
) -> list[ChatMessage]:
    """Fetch all messages for a session, ordered by creation time."""
    # Verify session belongs to user
    session_result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id, ChatSession.user_id == user_id
        )
    )
    session = session_result.scalar_one_or_none()
    if session is None:
        return []

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    return list(result.scalars().all())


async def delete_session(
    db: AsyncSession, session_id: UUID, user_id: str
) -> bool:
    """Delete a session and all its messages. Returns True if found."""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id, ChatSession.user_id == user_id
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        return False

    await db.delete(session)
    await db.commit()
    return True
