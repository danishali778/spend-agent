from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import (
    AgentRunRow,
    AgentStepRow,
    DecisionRow,
    DocumentRow,
    ExtractedFactRow,
    GeneratedArtifactRow,
    PolicyCheckRow,
    UsageSnapshotRow,
)
from app.schemas.api import AgentActivityEventResponse, AnalyzeCaseResponse, DecisionBlocker, DecisionEvidenceItem, DecisionResponse, GeneratedArtifactResponse, GetActivityResponse
from app.schemas.domain import AgentActivityEvent, CommsAgentResult, DecisionPacket, DocumentAnalysisResult, FinanceAnalysisResult, PolicyEvaluationResult, RunFailureCategory


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_latest_run(session: Session, case_id: str) -> AgentRunRow | None:
    return session.scalars(select(AgentRunRow).where(AgentRunRow.case_id == case_id).order_by(AgentRunRow.created_at.desc()).limit(1)).first()


def create_run(session: Session, *, case_id: str, triggered_by_user_id: str, prompt_bundle_version: str) -> AnalyzeCaseResponse:
    row = AgentRunRow(id=str(uuid4()), case_id=case_id, status="queued", triggered_by_user_id=triggered_by_user_id, prompt_bundle_version=prompt_bundle_version)
    session.add(row)
    session.commit()
    session.refresh(row)
    return AnalyzeCaseResponse(runId=row.id, status=row.status)


def mark_run_started(session: Session, run_id: str) -> None:
    row = session.get(AgentRunRow, run_id)
    if row is None:
        return
    row.status = "running"
    row.started_at = utc_now()
    row.failure_reason = None
    session.add(row)
    session.commit()


def finish_run(session: Session, run_id: str, *, status: str, failure_reason: str | None = None, failure_category: str | None = None) -> None:
    row = session.get(AgentRunRow, run_id)
    if row is None:
        return
    row.status = status
    row.completed_at = utc_now()
    row.failure_reason = failure_reason
    row.failure_category = failure_category
    session.add(row)
    session.commit()


def record_step(
    session: Session,
    *,
    run_id: str,
    agent_name: str,
    step_name: str,
    status: str,
    retry_count: int,
    summary: str | None,
    error_json: dict | None = None,
    existing_step_id: str | None = None,
) -> str:
    if existing_step_id:
        row = session.get(AgentStepRow, existing_step_id)
        if row is None:
            raise ValueError(f"Agent step {existing_step_id} not found")
        row.status = status
        row.summary = summary
        row.retry_count = retry_count
        row.error_json = error_json
        row.completed_at = utc_now()
        session.add(row)
        session.commit()
        return row.id
    row = AgentStepRow(
        id=str(uuid4()),
        run_id=run_id,
        agent_name=agent_name,
        step_name=step_name,
        status=status,
        summary=summary,
        retry_count=retry_count,
        error_json=error_json,
        started_at=utc_now(),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row.id


def persist_document_result(session: Session, *, case_id: str, run_id: str, result: DocumentAnalysisResult) -> None:
    rows = [
        ExtractedFactRow(
            id=str(uuid4()),
            case_id=case_id,
            document_id=fact.source_document_id,
            fact_key=fact.fact_key,
            fact_value_json=fact.value,
            source_snippet=fact.source_snippet,
            source_page=None,
            confidence_score=Decimal(str(fact.confidence_score)),
            provenance_kind=fact.provenance_kind.value,
            provenance_note=fact.provenance_note,
            extracted_by_run_id=run_id,
        )
        for fact in result.facts
    ]
    session.add_all(rows)
    session.commit()


def persist_finance_result(session: Session, *, case_id: str, run_id: str, result: FinanceAnalysisResult) -> None:
    snapshot = result.usage_snapshot
    session.add(
        UsageSnapshotRow(
            id=str(uuid4()),
            case_id=case_id,
            seats_purchased=snapshot.seats_purchased,
            seats_active=snapshot.seats_active,
            utilization_percent=Decimal(str(snapshot.utilization_percent)) if snapshot.utilization_percent is not None else None,
            cost_period=snapshot.cost_period,
            total_cost=Decimal(str(snapshot.total_cost)) if snapshot.total_cost is not None else None,
            currency=snapshot.currency,
            snapshot_source="merged",
            created_by_run_id=run_id,
        )
    )
    session.commit()


def persist_policy_results(session: Session, *, case_id: str, run_id: str, result: PolicyEvaluationResult) -> None:
    rows = [
        PolicyCheckRow(
            id=str(uuid4()),
            case_id=case_id,
            run_id=run_id,
            proposed_action="escalate" if result.requires_escalation else "renegotiate",
            threshold_name=check.threshold_name,
            result=check.result,
            message=check.message,
        )
        for check in result.checks
    ]
    session.add_all(rows)
    session.commit()


def persist_decision(session: Session, *, case_id: str, run_id: str, decision: DecisionPacket) -> tuple[str, int]:
    latest_version = session.scalar(select(func.max(DecisionRow.decision_version)).where(DecisionRow.case_id == case_id)) or 0
    decision_version = int(latest_version) + 1
    row = DecisionRow(
        id=str(uuid4()),
        case_id=case_id,
        run_id=run_id,
        decision_version=decision_version,
        recommended_action=decision.recommended_action.value,
        fallback_action=decision.fallback_action.value if decision.fallback_action else None,
        confidence_score=Decimal(str(decision.confidence_score)),
        rationale=decision.rationale,
        projected_savings=Decimal(str(decision.projected_savings)) if decision.projected_savings is not None else None,
        projected_savings_status=decision.projected_savings_status.value,
        blockers_json=decision.blockers,
        next_step=decision.next_step,
        evidence_json=[item.to_state_dict() for item in decision.evidence],
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row.id, row.decision_version


def persist_artifacts(session: Session, *, case_id: str, decision_id: str, artifacts: CommsAgentResult) -> None:
    rows = [
        GeneratedArtifactRow(
            id=str(uuid4()),
            case_id=case_id,
            decision_id=decision_id,
            artifact_type=artifact.artifact_type.value,
            title=artifact.title,
            content=artifact.content,
        )
        for artifact in artifacts.artifacts
    ]
    session.add_all(rows)
    session.commit()


def get_activity_response(session: Session, *, case_id: str, run_id: str | None = None) -> GetActivityResponse | None:
    run = session.get(AgentRunRow, run_id) if run_id else get_latest_run(session, case_id)
    if run is None:
        return None
    steps = session.scalars(select(AgentStepRow).where(AgentStepRow.run_id == run.id).order_by(AgentStepRow.started_at.asc())).all()
    return GetActivityResponse(
        runId=run.id,
        status=run.status,
        events=[AgentActivityEventResponse(runId=step.run_id, agentName=step.agent_name, stepName=step.step_name, status=step.status, startedAt=step.started_at.isoformat() if step.started_at else None, completedAt=step.completed_at.isoformat() if step.completed_at else None, summary=step.summary or "", error=step.error_json) for step in steps],
        failureReason=run.failure_reason,
        failureCategory=run.failure_category,
    )


class SqlAlchemyPersistenceHook:
    def __init__(self, session: Session, case_id: str, run_id: str) -> None:
        self.session = session
        self.case_id = case_id
        self.run_id = run_id
        self.step_row_ids: dict[str, str] = {}
        self.latest_decision_id: str | None = None
        self.failure_reason: str | None = None
        self.failure_category: RunFailureCategory | None = None

    def start_run(self, run_id: str, case, prompt_bundle_version: str) -> None:
        mark_run_started(self.session, run_id)

    def record_step(self, run_id: str, agent_name: str, step_name: str, status: str, retry_count: int, summary: str | None, error: dict | None = None) -> None:
        key = f"{agent_name}:{step_name}"
        if status == "running":
            self.step_row_ids[key] = record_step(self.session, run_id=run_id, agent_name=agent_name, step_name=step_name, status=status, retry_count=retry_count, summary=summary, error_json=error)
            return
        record_step(self.session, run_id=run_id, agent_name=agent_name, step_name=step_name, status=status, retry_count=retry_count, summary=summary, error_json=error, existing_step_id=self.step_row_ids.get(key))

    def persist_document_result(self, run_id: str, result: DocumentAnalysisResult) -> None:
        persist_document_result(self.session, case_id=self.case_id, run_id=run_id, result=result)

    def persist_finance_result(self, run_id: str, result: FinanceAnalysisResult) -> None:
        persist_finance_result(self.session, case_id=self.case_id, run_id=run_id, result=result)

    def persist_policy_results(self, run_id: str, result: PolicyEvaluationResult) -> None:
        persist_policy_results(self.session, case_id=self.case_id, run_id=run_id, result=result)

    def persist_decision(self, run_id: str, decision: DecisionPacket) -> None:
        self.latest_decision_id, _ = persist_decision(self.session, case_id=self.case_id, run_id=run_id, decision=decision)

    def persist_artifacts(self, run_id: str, artifacts) -> None:
        if self.latest_decision_id:
            persist_artifacts(self.session, case_id=self.case_id, decision_id=self.latest_decision_id, artifacts=artifacts)

    def finish_run(self, run_id: str, status: str) -> None:
        finish_run(self.session, run_id, status=status, failure_reason=self.failure_reason, failure_category=self.failure_category.value if self.failure_category else None)

    def update_case_summary(self, *, status: str, projected_savings: float | None, projected_savings_status: str, recommended_action: str | None, urgency_level: str | None = None) -> None:
        from app.repositories.cases import update_case_status
        update_case_status(self.session, self.case_id, status=status, projected_savings=projected_savings, projected_savings_status=projected_savings_status, recommended_action=recommended_action, urgency_level=urgency_level)

    def get_activity(self, run_id: str) -> list[AgentActivityEvent]:
        response = get_activity_response(self.session, case_id=self.case_id, run_id=run_id)
        if response is None:
            return []
        return [AgentActivityEvent(run_id=event.runId, agent_name=event.agentName, step_name=event.stepName, status=event.status, started_at=event.startedAt, completed_at=event.completedAt, summary=event.summary) for event in response.events]

    def snapshot(self, run_id: str) -> dict:
        response = get_activity_response(self.session, case_id=self.case_id, run_id=run_id)
        return {"status": response.status if response else "unknown", "activity": [event.model_dump() for event in response.events] if response else []}
