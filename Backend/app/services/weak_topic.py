from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import List

from app.models.weak_topic import WeakTopic

async def get_weak_topics(db: AsyncSession, user_id: UUID) -> List[WeakTopic]:
    stmt = (
        select(WeakTopic)
        .where(WeakTopic.user_id == user_id)
        .order_by(WeakTopic.frequency.desc(), WeakTopic.last_encountered.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
