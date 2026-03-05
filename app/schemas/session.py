from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MessageOut(BaseModel):
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionHistory(BaseModel):
    session_id: UUID
    messages: list[MessageOut]
