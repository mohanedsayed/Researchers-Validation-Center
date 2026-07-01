import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserTier(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    SCHOLAR = "scholar"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    language_preference: Mapped[str] = mapped_column(String(10), default="ar")
    tier: Mapped[UserTier] = mapped_column(Enum(UserTier), default=UserTier.FREE)
    monthly_token_balance: Mapped[int] = mapped_column(Integer, default=0)
    credit_balance: Mapped[int] = mapped_column(Integer, default=0)
    byok_api_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
