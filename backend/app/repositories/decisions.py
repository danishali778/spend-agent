from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DecisionRow, DocumentRow
from app.schemas.api import DecisionBlocker, DecisionEvidenceItem, DecisionPacketResponse, DecisionResponse


def get_latest_decision(session: Session, case_id: str, *, run_id: str | None = None) -> DecisionResponse | None:
    query = select(DecisionRow).where(DecisionRow.case_id == case_id)
    if run_id is not None:
        query = query.where(DecisionRow.run_id == run_id)
    row = session.scalars(query.order_by(DecisionRow.decision_version.desc()).limit(1)).first()
    if row is None:
        return None
    documents = {
        document.id: document.source_name
        for document in session.scalars(select(DocumentRow).where(DocumentRow.case_id == case_id)).all()
    }
    evidence = []
    for item in row.evidence_json or []:
        document_id = str(item.get("documentId") or item.get("sourceDocumentId", "unknown"))
        evidence.append(DecisionEvidenceItem(factKey=str(item.get("factKey", "unknown")), value=item.get("value"), documentId=document_id, sourceName=documents.get(document_id), snippet=str(item.get("snippet") or item.get("sourceSnippet", "")), confidenceScore=float(item.get("confidenceScore") or item.get("confidence_score") or 0), provenanceKind=item.get("provenanceKind")))
    blockers = []
    for index, item in enumerate(row.blockers_json or []):
        if isinstance(item, str):
            blockers.append(DecisionBlocker(code=f"blocker_{index + 1}", message=item))
        else:
            blockers.append(DecisionBlocker(code=str(item.get("code", f"blocker_{index + 1}")), message=str(item.get("message", "Unknown blocker"))))
    return DecisionResponse(
        decisionVersion=row.decision_version,
        decision=DecisionPacketResponse(
            recommendedAction=row.recommended_action,
            confidenceScore=float(row.confidence_score),
            rationale=row.rationale,
            evidence=evidence,
            projectedSavings=float(row.projected_savings) if row.projected_savings is not None else None,
            projectedSavingsStatus=row.projected_savings_status,
            blockers=blockers,
            nextStep=row.next_step,
            fallbackAction=row.fallback_action,
        ),
    )
