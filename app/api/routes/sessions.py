from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.session import MessageOut, SessionHistory
from app.services.db_service import delete_session, get_session_history

router = APIRouter()


@router.get("/sessions/{session_id}/history", response_model=SessionHistory)
async def get_history(
    session_id: UUID,
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Return a session's full message history."""
    messages = await get_session_history(db, session_id, user_id)
    return SessionHistory(
        session_id=session_id,
        messages=[
            MessageOut(
                role=m.role.value if hasattr(m.role, "value") else m.role,
                content=m.content,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )


@router.delete("/sessions/{session_id}", status_code=204)
async def remove_session(
    session_id: UUID,
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Delete a session and all its messages."""
    deleted = await delete_session(db, session_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return Response(status_code=204)
