import asyncio
from datetime import datetime, timezone

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.session import CritiqueSession, UploadedFile
from app.services.storage import storage_service
from app.tasks.celery_app import celery_app

engine = create_async_engine(settings.database_url)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def cleanup_expired_sessions_async():
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        result = await db.scalars(
            select(CritiqueSession).where(CritiqueSession.expires_at <= now)
        )
        expired_sessions = result.all()

        for session in expired_sessions:
            # Delete file from S3
            upload = await db.scalar(select(UploadedFile).where(UploadedFile.session_id == session.id))
            if upload:
                try:
                    storage_service.delete_file(upload.s3_key)
                except Exception:
                    pass
            
            # Delete from DB
            await db.delete(session)
        
        await db.commit()

@celery_app.task(name="app.tasks.cleanup.cleanup_expired_sessions")
def cleanup_expired_sessions():
    asyncio.run(cleanup_expired_sessions_async())
