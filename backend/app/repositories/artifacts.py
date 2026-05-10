from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DecisionRow, GeneratedArtifactRow
from app.schemas.api import GeneratedArtifactResponse


def get_artifacts(session: Session, case_id: str, *, run_id: str | None = None) -> list[GeneratedArtifactResponse] | None:
    query = select(DecisionRow).where(DecisionRow.case_id == case_id)
    if run_id is not None:
        query = query.where(DecisionRow.run_id == run_id)
    decision = session.scalars(query.order_by(DecisionRow.decision_version.desc()).limit(1)).first()
    if decision is None:
        return None
    rows = session.scalars(select(GeneratedArtifactRow).where(GeneratedArtifactRow.decision_id == decision.id).order_by(GeneratedArtifactRow.created_at.asc())).all()
    return [GeneratedArtifactResponse(artifactType=row.artifact_type, title=row.title, content=row.content, decisionVersion=decision.decision_version, createdAt=row.created_at.isoformat() if row.created_at else None) for row in rows]
