from __future__ import annotations

from typing import Any, Mapping

from app.agents.base import BaseSpecialistAgent
from app.schemas.domain import FinanceAnalysisResult


class FinanceAgent(BaseSpecialistAgent[FinanceAnalysisResult]):
    agent_name = "FinanceAgent"
    prompt_name = "finance-analysis"

    def __init__(self, provider_client) -> None:
        super().__init__(provider_client, FinanceAnalysisResult.from_agent_dict)

    def build_payload(self, state: Mapping[str, Any]) -> dict[str, Any]:
        return {"case": state["case"], "documents": state["documents"], "documentAnalysis": state.get("document_analysis")}
