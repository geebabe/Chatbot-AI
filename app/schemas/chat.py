from uuid import UUID

from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: UUID
    user_id: str
    message: str
