from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.analysis_service import AnalysisService
from app.services.case_service import CaseService
from app.services.document_service import DocumentService


def get_db() -> Generator[Session | None, None, None]:
    if SessionLocal is None:
        yield None
        return
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_case_service() -> CaseService:
    return CaseService()


def get_document_service() -> DocumentService:
    return DocumentService()


def get_analysis_service() -> AnalysisService:
    return AnalysisService()
