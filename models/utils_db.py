from models.models import Conversation, Role
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from sqlalchemy.future import select
from typing import List

async def add_conversation(session: AsyncSession, chat_id: str, role: Role, content: str):
    conversation = Conversation(
        role=role,
        content=content,
        chat_id=chat_id,
        created_at=datetime.now(timezone.utc)
    )
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return conversation

async def get_conversation_history_by_chat_id(
    session: AsyncSession,
    chat_id: str
) -> List[dict]:
    result = await session.execute(
        select(Conversation)
        .where(Conversation.chat_id == chat_id)
        .order_by(Conversation.created_at.asc())
    )
    records = result.scalars().all()

    return [{"role": r.role.value, "content": r.content} for r in records]