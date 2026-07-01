from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Will import routers and database later
# from app.api import auth, upload, sessions
# from app.database import engine
# from app.models import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    yield
    # await engine.dispose()

app = FastAPI(title="Naqqad API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import auth, upload, sessions

app.include_router(upload.router, prefix="/sessions", tags=["sessions"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])

app.include_router(auth.router, prefix="/auth", tags=["auth"])

@app.get("/health")
async def health():
    return {"status": "ok"}
