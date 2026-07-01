import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SessionStatus(str, enum.Enum):
    UPLOADING = "uploading"
    PARSING = "parsing"
    QUEUED = "queued"
    CRITIQUING = "critiquing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class CritiqueTone(str, enum.Enum):
    CONSTRUCTIVE = "constructive"
    FORENSIC = "forensic"


class ReportDepth(str, enum.Enum):
    EXECUTIVE = "executive"
    STANDARD = "standard"
    DEEP_AUDIT = "deep_audit"


class CritiqueSession(Base):
    __tablename__ = "critique_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus), default=SessionStatus.UPLOADING, nullable=False
    )
    tone: Mapped[CritiqueTone] = mapped_column(Enum(CritiqueTone), nullable=False)
    report_depth: Mapped[ReportDepth] = mapped_column(Enum(ReportDepth), nullable=False)
    detected_language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    detected_disciplines: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    jury_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tokens_consumed: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("critique_sessions.id"), nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_format: Mapped[str] = mapped_column(String(10), nullable=False)  # docx, txt, md
    s3_key: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    page_count_estimate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
