from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DocumentRow
from app.schemas.api import DocumentSummary


def create_document(
    session: Session,
    *,
    case_id: str,
    type: str,
    source_name: str,
    storage_path: str | None,
    raw_text: str | None,
    mime_type: str | None,
    parse_status: str,
) -> DocumentSummary:
    row = DocumentRow(
        id=str(uuid4()),
        case_id=case_id,
        type=type,
        source_name=source_name,
        storage_path=storage_path,
        raw_text=raw_text,
        mime_type=mime_type,
        parse_status=parse_status,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return DocumentSummary(id=row.id, type=row.type, sourceName=row.source_name, parseStatus=row.parse_status)


def list_document_rows_for_case(session: Session, case_id: str) -> list[DocumentRow]:
    return list(session.scalars(select(DocumentRow).where(DocumentRow.case_id == case_id).order_by(DocumentRow.uploaded_at.asc())).all())


def update_document_parse_result(session: Session, document_id: str, *, raw_text: str | None, parse_status: str) -> None:
    row = session.get(DocumentRow, document_id)
    if row is None:
        return
    row.raw_text = raw_text
    row.parse_status = parse_status
    session.add(row)
    session.commit()
