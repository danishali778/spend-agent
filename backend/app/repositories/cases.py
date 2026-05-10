from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AgentRunRow, CaseRow, DocumentRow
from app.schemas.api import CaseDetail, CaseSummary, DocumentSummary, GetCaseResponse


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _case_summary(row: CaseRow) -> CaseSummary:
    return CaseSummary(
        id=row.id,
        vendorName=row.vendor_name,
        status=row.status,
        renewalDate=_iso(row.renewal_date),
        urgencyLevel=row.urgency_level,
        projectedSavings=float(row.projected_savings) if row.projected_savings is not None else None,
        projectedSavingsStatus=row.projected_savings_status,
        recommendedAction=row.recommended_action,
    )


def list_cases(session: Session) -> list[CaseSummary]:
    rows = session.scalars(select(CaseRow).order_by(CaseRow.created_at.desc())).all()
    return [_case_summary(row) for row in rows]


def get_case_row(session: Session, case_id: str) -> CaseRow | None:
    return session.get(CaseRow, case_id)


def create_case(session: Session, *, vendor_name: str, owner_user_id: str, renewal_date: datetime | None) -> CaseSummary:
    row = CaseRow(id=str(uuid4()), vendor_name=vendor_name, owner_user_id=owner_user_id, renewal_date=renewal_date, status="draft")
    session.add(row)
    session.commit()
    session.refresh(row)
    return _case_summary(row)


def get_case_detail(session: Session, case_id: str) -> GetCaseResponse | None:
    row = session.get(CaseRow, case_id)
    if row is None:
        return None
    documents = session.scalars(select(DocumentRow).where(DocumentRow.case_id == case_id).order_by(DocumentRow.uploaded_at.asc())).all()
    latest_run = session.scalars(select(AgentRunRow).where(AgentRunRow.case_id == case_id).order_by(AgentRunRow.created_at.desc()).limit(1)).first()
    summary = _case_summary(row)
    return GetCaseResponse(
        case=CaseDetail(
            **summary.model_dump(),
            ownerUserId=row.owner_user_id,
            notes=None,
            createdAt=_iso(row.created_at) or "",
            updatedAt=_iso(row.updated_at) or "",
        ),
        documents=[DocumentSummary(id=document.id, type=document.type, sourceName=document.source_name, parseStatus=document.parse_status) for document in documents],
        latestRunId=latest_run.id if latest_run else None,
        latestRunStatus=latest_run.status if latest_run else None,
        latestRunFailureReason=latest_run.failure_reason if latest_run else None,
        latestRunFailureCategory=latest_run.failure_category if latest_run else None,
    )


def update_case_status(
    session: Session,
    case_id: str,
    *,
    status: str,
    projected_savings: float | None = None,
    projected_savings_status: str = "not_available",
    recommended_action: str | None = None,
    urgency_level: str | None = None,
) -> None:
    row = session.get(CaseRow, case_id)
    if row is None:
        return
    row.status = status
    row.projected_savings = Decimal(str(projected_savings)) if projected_savings is not None else None
    row.projected_savings_status = projected_savings_status
    row.recommended_action = recommended_action
    if urgency_level is not None:
        row.urgency_level = urgency_level
    session.add(row)
    session.commit()
