from __future__ import annotations

from typing import Any, Mapping

from app.agents.base import BaseSpecialistAgent
from app.schemas.domain import ArtifactType, CommsAgentResult


class CommsAgent(BaseSpecialistAgent[CommsAgentResult]):
    agent_name = "CommsAgent"
    prompt_name = "artifact-generation"

    def __init__(self, provider_client) -> None:
        super().__init__(provider_client, CommsAgentResult.from_agent_dict)

    def build_payload(self, state: Mapping[str, Any]) -> dict[str, Any]:
        return {"case": state["case"], "decision": state["decision"], "documentAnalysis": state.get("document_analysis")}

    def validate_result(self, result: CommsAgentResult, payload: Mapping[str, Any]) -> None:
        expected_types = {
            ArtifactType.CFO_SUMMARY,
            ArtifactType.APPROVAL_NOTE,
            ArtifactType.VENDOR_EMAIL,
        }
        actual_types = {artifact.artifact_type for artifact in result.artifacts}
        if len(result.artifacts) != 3 or actual_types != expected_types:
            raise ValueError("artifacts must include exactly cfo_summary, approval_note, and vendor_email.")
        for artifact in result.artifacts:
            if not artifact.title.strip():
                raise ValueError("artifact titles must be non-empty.")
            if not artifact.content.strip():
                raise ValueError("artifact content must be non-empty.")
