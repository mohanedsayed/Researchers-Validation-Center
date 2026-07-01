from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.session import CritiqueSession, SessionStatus, UploadedFile, CritiqueTone, ReportDepth
from app.models.user import User
from app.schemas.session import SessionResponse
from app.services.storage import storage_service
from app.tasks.chunking import process_document
from app.config import settings

# A placeholder dependency to get the current user (US2 implementation detail)
async def get_current_user(db: AsyncSession = Depends(get_db)) -> User:
    # MVP: Returning a dummy user for now if no auth is sent, 
    # but in real life it decodes JWT
    from sqlalchemy import select
    user = await db.scalar(select(User).limit(1))
    if not user:
        user = User(email="dummy@example.com", hashed_password="dummy")
        db.add(user)
        await db.commit()
    return user

router = APIRouter()

@router.post("/upload", response_model=SessionResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    tone: CritiqueTone = Form(...),
    report_depth: ReportDepth = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validation
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["txt", "md", "docx"]:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    # Upload to S3
    s3_key = storage_service.upload_encrypted(file.file, file.filename)

    # Create Session
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.session_ttl_hours)
    session = CritiqueSession(
        user_id=current_user.id,
        tone=tone,
        report_depth=report_depth,
        status=SessionStatus.UPLOADING,
        expires_at=expires_at,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    # Create UploadedFile record
    uploaded_file = UploadedFile(
        session_id=session.id,
        original_filename=file.filename,
        file_format=ext,
        s3_key=s3_key,
        file_size_bytes=0, # ideally read from spool
    )
    db.add(uploaded_file)
    await db.commit()

    # Trigger Celery task
    process_document.delay(str(session.id))

    return SessionResponse(
        id=session.id,
        status=session.status,
        tone=session.tone,
        report_depth=session.report_depth,
        created_at=session.created_at,
    )
