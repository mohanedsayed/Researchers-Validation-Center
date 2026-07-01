import asyncio
import os
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.session import CritiqueSession, SessionStatus, UploadedFile
from app.models.chunk import Chunk
from app.services.storage import storage_service
from app.services.file_parser import parse_file
from app.services.chunker import chunker
from app.tasks.celery_app import celery_app

engine = create_async_engine(settings.database_url)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def process_document_async(session_id: str):
    async with AsyncSessionLocal() as db:
        session = await db.scalar(select(CritiqueSession).where(CritiqueSession.id == uuid.UUID(session_id)))
        if not session:
            return

        session.status = SessionStatus.PARSING
        await db.commit()

        # Find the file
        upload = await db.scalar(select(UploadedFile).where(UploadedFile.session_id == session.id))
        if not upload:
            session.status = SessionStatus.FAILED
            await db.commit()
            return

        # Download from S3 and decrypt
        temp_path = f"/tmp/{uuid.uuid4()}_{upload.original_filename}"
        try:
            storage_service.download_decrypted(upload.s3_key, temp_path)
            
            # Parse
            text = parse_file(temp_path, upload.file_format)
            
            # Chunking
            chunks_data = await chunker.generate_chunks(text)
            
            # Save chunks
            for c_data in chunks_data:
                chunk = Chunk(
                    session_id=session.id,
                    paragraph_index=c_data["paragraph_index"],
                    text=c_data["text"],
                    chapter_title=c_data.get("chapter_title"),
                    section_title=c_data.get("section_title"),
                )
                db.add(chunk)
            
            session.status = SessionStatus.QUEUED
            await db.commit()
        except Exception as e:
            session.status = SessionStatus.FAILED
            await db.commit()
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

@celery_app.task(name="app.tasks.chunking.process_document")
def process_document(session_id: str):
    asyncio.run(process_document_async(session_id))
