from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as PgEnum
from .db import Base
from datetime import datetime, timezone

class Role(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    role = Column(PgEnum(Role), nullable=False)
    content = Column(Text, nullable=False)
    chat_id = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)) 