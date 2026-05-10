from __future__ import annotations

from celery import Celery

from .config import settings


celery_app = Celery(
    "spendagent-backend",
    broker=settings.redis_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.analysis", "app.tasks.documents"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=False,
)
