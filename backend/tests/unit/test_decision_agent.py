from __future__ import annotations

from app.agents.decision_agent import DecisionAgent
from app.schemas.domain import FactProvenanceKind
from app.services.provider_client import MockProviderClient


def test_decision_agent_hydrates_evidence_metadata_from_document_facts() -> None:
    agent = DecisionAgent(MockProviderClient())
    result = agent.parse_result(
        {
            "recommendedAction": "renegotiate",
            "confidenceScore": 0.81,
            "rationale": "Low utilization supports renegotiation.",
            "evidence": [
                {
                    "factKey": "renewal_date",
                    "value": "2026-11-15",
                    "sourceDocumentId": "doc-1",
                }
            ],
            "projectedSavings": 22560.0,
            "projectedSavingsStatus": "calculated",
            "blockers": [],
            "nextStep": "Initiate a discussion with the vendor.",
            "fallbackAction": "downgrade",
        }
    )

    payload = {
        "documentAnalysis": {
            "facts": [
                {
                    "factKey": "renewal_date",
                    "value": "2026-11-15",
                    "sourceDocumentId": "doc-1",
                    "sourceSnippet": "This agreement renews automatically on 2026-11-15.",
                    "confidenceScore": 0.94,
                    "provenanceKind": "extracted",
                }
            ]
        },
        "financeAnalysis": {
            "projectedSavingsStatus": "calculated",
            "savingsScenarios": [
                {
                    "projectedSavings": 22560.0,
                    "projectedSavingsStatus": "calculated",
                }
            ],
        },
    }

    agent.validate_result(result, payload)

    assert result.evidence[0].source_snippet == "This agreement renews automatically on 2026-11-15."
    assert result.evidence[0].confidence_score == 0.94
    assert result.evidence[0].provenance_kind == FactProvenanceKind.EXTRACTED
