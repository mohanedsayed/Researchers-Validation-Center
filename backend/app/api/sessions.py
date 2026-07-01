import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.session import CritiqueSession
from app.models.chunk import Chunk
from app.schemas.session import SessionResponse
from app.schemas.chunk import ChunkResponse
from app.models.user import User

# Same dummy auth for now
async def get_current_user(db: AsyncSession = Depends(get_db)) -> User:
    user = await db.scalar(select(User).limit(1))
    return user

router = APIRouter()

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = await db.scalar(select(CritiqueSession).where(CritiqueSession.id == session_id))
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(
        id=session.id,
        status=session.status,
        tone=session.tone,
        report_depth=session.report_depth,
        created_at=session.created_at,
    )

@router.get("/{session_id}/chunks", response_model=list[ChunkResponse])
async def get_session_chunks(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = await db.scalar(select(CritiqueSession).where(CritiqueSession.id == session_id))
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.scalars(
        select(Chunk).where(Chunk.session_id == session_id).order_by(Chunk.paragraph_index)
    )
    chunks = result.all()
    return [
        ChunkResponse(
            id=c.id,
            paragraph_index=c.paragraph_index,
            text=c.text,
            critique_status=c.critique_status
        ) for c in chunks
    ]
