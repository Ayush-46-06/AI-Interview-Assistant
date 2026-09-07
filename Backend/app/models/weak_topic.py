import uuid
from sqlalchemy import String, Integer, DECIMAL, DateTime, ForeignKey, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base

class WeakTopic(Base):
    __tablename__ = "weak_topics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    topic: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    frequency: Mapped[int] = mapped_column(
        Integer, default=1, server_default=text("1"), nullable=False
    )
    avg_score: Mapped[float | None] = mapped_column(DECIMAL(5, 2), nullable=True)
    last_encountered: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="weak_topics")
