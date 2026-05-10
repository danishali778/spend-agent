from __future__ import annotations

from dataclasses import dataclass, field

from app.orchestrator.run_manager import AgentRunManager
from app.schemas.domain import CaseRecord, DocumentRecord, DocumentType, ProjectedSavingsStatus
from app.services.provider_client import MockProviderClient


@dataclass
class RecordingPersistenceHook:
    case_status_updates: list[dict[str, object]] = field(default_factory=list)
    decision = None
    activity: list[object] = field(default_factory=list)

    def start_run(self, run_id: str, case, prompt_bundle_version: str) -> None:
        return None

    def record_step(self, run_id: str, agent_name: str, step_name: str, status: str, retry_count: int, summary: str | None, error: dict | None = None) -> None:
        return None

    def persist_document_result(self, run_id: str, result) -> None:
        return None

    def persist_finance_result(self, run_id: str, result) -> None:
        return None

    def persist_policy_results(self, run_id: str, result) -> None:
        return None

    def persist_decision(self, run_id: str, decision) -> None:
        self.decision = decision

    def persist_artifacts(self, run_id: str, artifacts) -> None:
        return None

    def finish_run(self, run_id: str, status: str) -> None:
        return None

    def update_case_summary(self, *, status: str, projected_savings: float | None, projected_savings_status: str, recommended_action: str | None, urgency_level: str | None = None) -> None:
        self.case_status_updates.append(
            {
                "status": status,
                "projected_savings": projected_savings,
                "projected_savings_status": projected_savings_status,
                "recommended_action": recommended_action,
                "urgency_level": urgency_level,
            }
        )

    def get_activity(self, run_id: str) -> list[object]:
        return self.activity

    def snapshot(self, run_id: str) -> dict[str, object]:
        return {"status": "completed", "activity": []}


def _case() -> CaseRecord:
    return CaseRecord(
        id="case-1",
        vendor_name="Test Vendor",
        owner_user_id="user-1",
        status="draft",
        renewal_date="2026-12-01T00:00:00+00:00",
        urgency_level="medium",
        projected_savings=None,
        projected_savings_status=ProjectedSavingsStatus.NOT_AVAILABLE,
        recommended_action=None,
    )


def test_run_manager_preserves_needs_spend_data_without_escalation() -> None:
    provider = MockProviderClient()
    persistence = RecordingPersistenceHook()
    manager = AgentRunManager(provider_client=provider, persistence_hook=persistence)
    documents = [
        DocumentRecord(
            id="doc-email",
            case_id="case-1",
            type=DocumentType.RENEWAL_EMAIL,
            source_name="renewal-reminder",
            raw_text=(
                "Subject: Renewal Reminder\n\n"
                "Renews on 2026-12-01.\n"
                "Any downgrade or cancellation request must be submitted at least 14 days before the renewal date.\n"
                "Current plan details:\n"
                "- 120 business seats\n"
            ),
            parse_status="parsed",
        ),
        DocumentRecord(
            id="doc-usage",
            case_id="case-1",
            type=DocumentType.USAGE_CSV,
            source_name="usage.csv",
            raw_text="user_id,active,last_seen_at\nu1,true,2026-05-01\nu2,false,2026-03-01\n",
            parse_status="parsed",
        ),
    ]

    result = manager.execute(_case(), documents, run_id="run-1")

    assert result.decision.recommended_action.value == "renegotiate"
    assert result.decision.projected_savings_status.value == "needs_spend_data"
    assert persistence.case_status_updates[-1]["status"] == "decision_ready"
    assert persistence.case_status_updates[-1]["projected_savings_status"] == "needs_spend_data"


def test_run_manager_escalates_finance_conflicts() -> None:
    provider = MockProviderClient()
    persistence = RecordingPersistenceHook()
    manager = AgentRunManager(provider_client=provider, persistence_hook=persistence)
    documents = [
        DocumentRecord(
            id="doc-email",
            case_id="case-1",
            type=DocumentType.RENEWAL_EMAIL,
            source_name="renewal-reminder",
            raw_text=(
                "Subject: Renewal Reminder\n\n"
                "Renews on 2026-12-30.\n"
                "Any downgrade or cancellation request must be submitted at least 14 days before the renewal date.\n"
                "Current plan details:\n"
                "- 50 business seats\n"
                "- Annual contract value: $12,000\n"
            ),
            parse_status="parsed",
        ),
        DocumentRecord(
            id="doc-usage",
            case_id="case-1",
            type=DocumentType.USAGE_CSV,
            source_name="usage.csv",
            raw_text="user_id,active,last_seen_at\n" + "\n".join([f"u{i},true,2026-05-01" for i in range(1, 81)]) + "\n",
            parse_status="parsed",
        ),
    ]

    result = manager.execute(_case(), documents, run_id="run-2")

    assert result.decision.recommended_action.value == "escalate"
    assert result.decision.projected_savings_status.value == "not_available"
    assert persistence.case_status_updates[-1]["status"] == "needs_review"
    assert persistence.case_status_updates[-1]["projected_savings_status"] == "not_available"


class NoDecisionProvider(MockProviderClient):
    def generate_json(self, agent_name: str, prompt_name: str, payload):
        if agent_name == "DecisionAgent":
            raise AssertionError("DecisionAgent should not be called when requires_escalation is already set.")
        return super().generate_json(agent_name, prompt_name, payload)


def test_run_manager_skips_decision_provider_when_escalation_is_required() -> None:
    provider = NoDecisionProvider()
    persistence = RecordingPersistenceHook()
    manager = AgentRunManager(provider_client=provider, persistence_hook=persistence)
    documents = [
        DocumentRecord(
            id="doc-email",
            case_id="case-1",
            type=DocumentType.RENEWAL_EMAIL,
            source_name="renewal-reminder",
            raw_text=(
                "Subject: Renewal Reminder\n\n"
                "Renews on 2026-12-30.\n"
                "Any downgrade or cancellation request must be submitted at least 14 days before the renewal date.\n"
                "Current plan details:\n"
                "- 50 business seats\n"
                "- Annual contract value: $12,000\n"
            ),
            parse_status="parsed",
        ),
        DocumentRecord(
            id="doc-usage",
            case_id="case-1",
            type=DocumentType.USAGE_CSV,
            source_name="usage.csv",
            raw_text="user_id,active,last_seen_at\n" + "\n".join([f"u{i},true,2026-05-01" for i in range(1, 81)]) + "\n",
            parse_status="parsed",
        ),
    ]

    result = manager.execute(_case(), documents, run_id="run-3")

    assert result.decision.recommended_action.value == "escalate"
