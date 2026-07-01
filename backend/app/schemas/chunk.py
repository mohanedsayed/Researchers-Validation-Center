import uuid
from pydantic import BaseModel

class ChunkResponse(BaseModel):
    id: uuid.UUID
    paragraph_index: int
    text: str
    critique_status: str
