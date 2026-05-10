from __future__ import annotations

from app.core.celery_app import celery_app


@celery_app.task(name="app.tasks.documents.noop")
def noop_document_task(document_id: str) -> dict[str, str]:
    return {"documentId": document_id, "status": "noop"}
