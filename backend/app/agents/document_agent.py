from __future__ import annotations

from typing import Any, Mapping

from app.agents.base import BaseSpecialistAgent
from app.schemas.domain import DocumentAnalysisResult


class DocumentAgent(BaseSpecialistAgent[DocumentAnalysisResult]):
    agent_name = "DocumentAgent"
    prompt_name = "document-analysis"

    def __init__(self, provider_client) -> None:
        super().__init__(provider_client, DocumentAnalysisResult.from_agent_dict)

    def build_payload(self, state: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "case": state["case"],
            "documents": state["documents"],
            "allowMockFallbacks": state.get("allow_mock_fallbacks", False),
        }
