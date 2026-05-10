from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.agents.base import AgentSchemaError
from app.agents.comms_agent import CommsAgent
from app.agents.decision_agent import DecisionAgent
from app.agents.document_agent import DocumentAgent
from app.agents.finance_agent import FinanceAgent
from app.agents.policy_agent import PolicyAgent
from app.orchestrator.state_machine import RunStage, RunStateMachine
from app.schemas.domain import (
    AgentActivityEvent,
    CaseRecord,
    CommsAgentResult,
    DecisionPacket,
    DocumentRecord,
    FactProvenanceKind,
    ProjectedSavingsStatus,
    RecommendedAction,
    RunFailureCategory,
)
from app.services.provider_client import MockProviderClient, ProviderClient, ProviderResponseError, ProviderTransportError


@dataclass
class RunResult:
    run_id: str
    state_machine: RunStateMachine
    decision: DecisionPacket
    artifacts: CommsAgentResult
    activity: list[AgentActivityEvent]
    persisted_state: dict[str, Any]


class AgentRunManager:
    prompt_bundle_version = "v1.0.0"
    max_agent_retries = 1

    def __init__(self, provider_client: ProviderClient | None = None, persistence_hook=None) -> None:
        self.provider_client = provider_client or MockProviderClient()
        self.persistence_hook = persistence_hook
        self.document_agent = DocumentAgent(self.provider_client)
        self.finance_agent = FinanceAgent(self.provider_client)
        self.policy_agent = PolicyAgent(self.provider_client)
        self.decision_agent = DecisionAgent(self.provider_client)
        self.comms_agent = CommsAgent(self.provider_client)

    def execute(self, case: CaseRecord, documents: list[DocumentRecord], run_id: str) -> RunResult:
        state_machine = RunStateMachine()
        self.persistence_hook.start_run(run_id=run_id, case=case, prompt_bundle_version=self.prompt_bundle_version)

        state: dict[str, Any] = {
            "case": case.to_state_dict(),
            "documents": [document.to_state_dict() for document in documents],
            "requires_escalation": False,
            "escalation_reasons": [],
            "allow_mock_fallbacks": isinstance(self.provider_client, MockProviderClient),
        }

        try:
            self._complete_internal_stage(state_machine, run_id, RunStage.INPUT_PREP, "Prepared run inputs and document inventory.")

            document_analysis = self._execute_specialist_stage(state_machine, run_id, RunStage.DOCUMENT_ANALYSIS, state, self.document_agent.run)
            state["document_analysis"] = document_analysis.to_state_dict()
            self.persistence_hook.persist_document_result(run_id, document_analysis)
            if document_analysis.missing_critical_facts:
                state["requires_escalation"] = True
                state["escalation_reasons"] = [f"Missing critical facts: {', '.join(document_analysis.missing_critical_facts)}"]

            finance_analysis = self._execute_specialist_stage(state_machine, run_id, RunStage.FINANCE_ANALYSIS, state, self.finance_agent.run)
            state["finance_analysis"] = finance_analysis.to_state_dict()
            self.persistence_hook.persist_finance_result(run_id, finance_analysis)
            if finance_analysis.conflicts:
                state["requires_escalation"] = True
                state["escalation_reasons"].extend(finance_analysis.conflicts)

            policy_evaluation = self._execute_specialist_stage(state_machine, run_id, RunStage.POLICY_CHECK, state, self.policy_agent.run)
            state["policy_evaluation"] = policy_evaluation.to_state_dict()
            self.persistence_hook.persist_policy_results(run_id, policy_evaluation)
            if policy_evaluation.requires_escalation:
                state["requires_escalation"] = True
                state["escalation_reasons"].append("Policy checks require escalation.")

            decision = self._execute_decision_stage(state_machine, run_id, state)
            state["decision"] = decision.to_state_dict()
            self.persistence_hook.persist_decision(run_id, decision)

            artifacts = self._execute_specialist_stage(state_machine, run_id, RunStage.ARTIFACT_GENERATION, state, self.comms_agent.run)
            self.persistence_hook.persist_artifacts(run_id, artifacts)

            self._complete_internal_stage(state_machine, run_id, RunStage.PERSISTENCE, "Persisted decision packet, artifacts, and timeline events.")
            self.persistence_hook.finish_run(run_id=run_id, status="completed")
            case_status = "needs_review" if decision.recommended_action == RecommendedAction.ESCALATE else "decision_ready"
            self.persistence_hook.update_case_summary(status=case_status, projected_savings=decision.projected_savings, projected_savings_status=decision.projected_savings_status.value, recommended_action=decision.recommended_action.value, urgency_level=case.urgency_level)

            return RunResult(run_id=run_id, state_machine=state_machine, decision=decision, artifacts=artifacts, activity=self.persistence_hook.get_activity(run_id), persisted_state=self.persistence_hook.snapshot(run_id))
        except Exception as exc:  # noqa: BLE001
            self.persistence_hook.failure_reason = str(exc)
            self.persistence_hook.failure_category = self._failure_category_for_exception(exc)
            self.persistence_hook.finish_run(run_id=run_id, status="failed")
            self.persistence_hook.update_case_summary(status="needs_review", projected_savings=None, projected_savings_status=ProjectedSavingsStatus.NOT_AVAILABLE.value, recommended_action=None, urgency_level=case.urgency_level)
            raise

    def _execute_decision_stage(self, state_machine: RunStateMachine, run_id: str, state: dict[str, Any]) -> DecisionPacket:
        if state.get("requires_escalation"):
            decision = self._build_escalation_decision(state)
            self._complete_internal_stage(state_machine, run_id, RunStage.DECISION, "Escalated decision due to missing critical evidence or policy constraints.", agent_name="DecisionAgent")
            return decision
        return self._execute_specialist_stage(state_machine, run_id, RunStage.DECISION, state, self.decision_agent.run)

    def _execute_specialist_stage(self, state_machine: RunStateMachine, run_id: str, stage: RunStage, state: dict[str, Any], executor):
        attempts = 0
        while True:
            attempts += 1
            state_machine.start_stage(stage)
            self.persistence_hook.record_step(run_id=run_id, agent_name=self._agent_name_for_stage(stage), step_name=stage.value, status="running", retry_count=attempts - 1, summary=f"Running {stage.value}.")
            try:
                result = executor(state)
            except AgentSchemaError as exc:
                retrying = attempts <= self.max_agent_retries
                state_machine.fail_stage(stage, error={"type": "schema_error", "message": str(exc)}, retrying=retrying)
                self.persistence_hook.record_step(run_id=run_id, agent_name=self._agent_name_for_stage(stage), step_name=stage.value, status="failed", retry_count=attempts, summary=str(exc), error={"type": "schema_error"})
                if retrying:
                    continue
                raise
            summary = self._summary_for_result(stage, result)
            state_machine.complete_stage(stage, summary=summary)
            self.persistence_hook.record_step(run_id=run_id, agent_name=self._agent_name_for_stage(stage), step_name=stage.value, status="completed", retry_count=attempts - 1, summary=summary)
            return result

    def _complete_internal_stage(self, state_machine: RunStateMachine, run_id: str, stage: RunStage, summary: str, agent_name: str = "OrchestratorAgent") -> None:
        state_machine.start_stage(stage)
        self.persistence_hook.record_step(run_id=run_id, agent_name=agent_name, step_name=stage.value, status="running", retry_count=0, summary=f"Running {stage.value}.")
        state_machine.complete_stage(stage, summary=summary)
        self.persistence_hook.record_step(run_id=run_id, agent_name=agent_name, step_name=stage.value, status="completed", retry_count=0, summary=summary)

    def _build_escalation_decision(self, state: dict[str, Any]) -> DecisionPacket:
        reasons = list(dict.fromkeys(state.get("escalation_reasons", [])))
        return DecisionPacket(
            recommended_action=RecommendedAction.ESCALATE,
            confidence_score=0.32,
            rationale="Escalated because the system cannot defend an autonomous recommendation safely.",
            evidence=[],
            projected_savings=None,
            projected_savings_status=ProjectedSavingsStatus.NOT_AVAILABLE,
            blockers=reasons or ["Critical evidence is missing."],
            next_step="Route the case to a human reviewer and request the missing evidence.",
            fallback_action=None,
        )

    def _failure_category_for_exception(self, exc: Exception) -> RunFailureCategory:
        if isinstance(exc, ProviderTransportError):
            return RunFailureCategory.PROVIDER_UNAVAILABLE
        if isinstance(exc, (ProviderResponseError, AgentSchemaError)):
            return RunFailureCategory.INVALID_MODEL_OUTPUT
        return RunFailureCategory.UNKNOWN

    def _agent_name_for_stage(self, stage: RunStage) -> str:
        return {
            RunStage.DOCUMENT_ANALYSIS: "DocumentAgent",
            RunStage.FINANCE_ANALYSIS: "FinanceAgent",
            RunStage.POLICY_CHECK: "PolicyAgent",
            RunStage.DECISION: "DecisionAgent",
            RunStage.ARTIFACT_GENERATION: "CommsAgent",
        }.get(stage, "OrchestratorAgent")

    def _summary_for_result(self, stage: RunStage, result: Any) -> str:
        if stage == RunStage.DOCUMENT_ANALYSIS:
            return f"Extracted {len(result.facts)} facts with {len(result.missing_critical_facts)} missing critical facts."
        if stage == RunStage.FINANCE_ANALYSIS:
            utilization = result.usage_snapshot.utilization_percent
            utilization_text = f"{utilization:.1f}%" if utilization is not None else "no utilization"
            return f"Computed {utilization_text} and {len(result.savings_scenarios)} savings scenarios."
        if stage == RunStage.POLICY_CHECK:
            return f"Evaluated {len(result.checks)} policy checks."
        if stage == RunStage.DECISION:
            return f"Selected {result.recommended_action.value} with confidence {result.confidence_score:.2f}."
        if stage == RunStage.ARTIFACT_GENERATION:
            return f"Generated {len(result.artifacts)} draft artifacts."
        return stage.value
