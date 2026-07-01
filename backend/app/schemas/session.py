import uuid
from datetime import datetime
from pydantic import BaseModel

class SessionCreate(BaseModel):
    tone: str
    report_depth: str
    detected_language: str | None = None

class SessionResponse(BaseModel):
    id: uuid.UUID
    status: str
    tone: str
    report_depth: str
    created_at: datetime
