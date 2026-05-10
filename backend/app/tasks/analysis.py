from __future__ import annotations

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.analysis_service import AnalysisService


@celery_app.task(name="app.tasks.analysis.analyze_case_run", bind=True)
def analyze_case_run(self, run_id: str, case_id: str) -> dict:
    if SessionLocal is None:
        raise RuntimeError("Database URL is not configured.")
    session = SessionLocal()
    try:
        service = AnalysisService()
        return service.execute_case_analysis(session, run_id, case_id)
    finally:
        session.close()
