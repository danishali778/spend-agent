from __future__ import annotations

from typing import Any, Mapping

from app.agents.base import BaseSpecialistAgent
from app.schemas.domain import PolicyEvaluationResult


class PolicyAgent(BaseSpecialistAgent[PolicyEvaluationResult]):
    agent_name = "PolicyAgent"
    prompt_name = "policy-check"

    def __init__(self, provider_client) -> None:
        super().__init__(provider_client, PolicyEvaluationResult.from_agent_dict)

    def build_payload(self, state: Mapping[str, Any]) -> dict[str, Any]:
        return {"case": state["case"], "financeAnalysis": state.get("finance_analysis"), "documentAnalysis": state.get("document_analysis")}
