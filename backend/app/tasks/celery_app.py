import os
from celery import Celery

from app.config import settings

celery_app = Celery(
    "naqqad_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.chunking", "app.tasks.cleanup"],
)

celery_app.conf.task_routes = {
    "app.tasks.chunking.*": {"queue": "chunking"},
    "app.tasks.cleanup.*": {"queue": "cleanup"},
}

celery_app.conf.beat_schedule = {
    "cleanup-every-hour": {
        "task": "app.tasks.cleanup.cleanup_expired_sessions",
        "schedule": 3600.0,
    },
}
