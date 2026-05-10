from __future__ import annotations

from typing import Any, Mapping

from app.agents.base import BaseSpecialistAgent
from app.schemas.domain import DecisionPacket, FactProvenanceKind


class DecisionAgent(BaseSpecialistAgent[DecisionPacket]):
    agent_name = "DecisionAgent"
    prompt_name = "decision"

    def __init__(self, provider_client) -> None:
        super().__init__(provider_client, DecisionPacket.from_agent_dict)

    def build_payload(self, state: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "case": state["case"],
            "documentAnalysis": state.get("document_analysis"),
            "financeAnalysis": state.get("finance_analysis"),
            "policyEvaluation": state.get("policy_evaluation"),
            "requiresEscalation": state.get("requires_escalation", False),
            "escalationReasons": state.get("escalation_reasons", []),
        }

    def validate_result(self, result: DecisionPacket, payload: Mapping[str, Any]) -> None:
        finance = payload.get("financeAnalysis") or {}
        scenarios = finance.get("savingsScenarios") or []
        expected_savings = scenarios[0].get("projectedSavings") if scenarios else None
        expected_status = finance.get("projectedSavingsStatus", "not_available")
        if scenarios and scenarios[0].get("projectedSavingsStatus"):
            expected_status = scenarios[0]["projectedSavingsStatus"]

        if result.projected_savings != expected_savings:
            raise ValueError("projectedSavings must preserve the deterministic finance output.")
        if result.projected_savings_status.value != expected_status:
            raise ValueError("projectedSavingsStatus must preserve the deterministic finance output.")
        if not result.rationale.strip():
            raise ValueError("rationale is required.")
        if not result.next_step.strip():
            raise ValueError("nextStep is required.")

        facts = (payload.get("documentAnalysis") or {}).get("facts", [])
        facts_by_pair = {
            (str(fact.get("factKey")), str(fact.get("sourceDocumentId"))): fact
            for fact in facts
        }
        allowed_pairs = {
            (fact_key, document_id)
            for fact_key, document_id in facts_by_pair
        }
        for item in result.evidence:
            if (item.fact_key, item.source_document_id) not in allowed_pairs:
                raise ValueError("evidence items must reference documentAnalysis facts only.")
            source_fact = facts_by_pair[(item.fact_key, item.source_document_id)]
            if item.value is None:
                item.value = source_fact.get("value")
            if not item.source_snippet:
                item.source_snippet = str(source_fact.get("sourceSnippet") or "")
            if item.confidence_score <= 0:
                item.confidence_score = float(source_fact.get("confidenceScore") or 0)
            if source_fact.get("provenanceKind"):
                item.provenance_kind = FactProvenanceKind(str(source_fact["provenanceKind"]))
