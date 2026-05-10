from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.agents.base import AgentSchemaError
from app.agents.comms_agent import CommsAgent
from app.agents.decision_agent import DecisionAgent
from app.schemas.domain import ArtifactType
from app.services.provider_client import (
    GeminiProviderClient,
    GroqProviderClient,
    MockProviderClient,
    ProviderResponseError,
    create_provider_client,
)


class StubProvider:
    def __init__(self, payload):
        self.payload = payload

    def generate_json(self, agent_name: str, prompt_name: str, payload):
        return self.payload


def _decision_payload() -> dict[str, object]:
    return {
        "case": {"vendorName": "Golden Path Vendor"},
        "documentAnalysis": {
            "facts": [
                {"factKey": "renewal_date", "value": "2026-11-15", "sourceDocumentId": "doc-email"},
                {"factKey": "seats_purchased", "value": 150, "sourceDocumentId": "doc-email"},
            ]
        },
        "financeAnalysis": {
            "usageSnapshot": {
                "seatsPurchased": 150,
                "seatsActive": 28,
                "utilizationPercent": 18.7,
                "totalCost": 36000,
                "costPeriod": "annual",
                "currency": "USD",
            },
            "projectedSavingsStatus": "calculated",
            "savingsScenarios": [
                {
                    "action": "renegotiate",
                    "projectedSavings": 22560.0,
                    "projectedSavingsStatus": "calculated",
                    "summary": "Renegotiating to align seat count with usage creates savings potential.",
                }
            ],
            "conflicts": [],
        },
        "policyEvaluation": {"checks": [], "requiresEscalation": False},
        "requiresEscalation": False,
        "escalationReasons": [],
    }


def test_create_provider_client_selects_modes() -> None:
    mock_settings = SimpleNamespace(provider_mode="mock")
    groq_settings = SimpleNamespace(
        provider_mode="groq",
        groq_api_key="test-key",
        groq_model="llama-test",
        groq_timeout_seconds=12.0,
        groq_temperature=0.2,
    )
    gemini_settings = SimpleNamespace(
        provider_mode="gemini",
        gemini_api_key="test-key",
        gemini_model="gemini-test",
        gemini_timeout_seconds=10.0,
        gemini_temperature=0.3,
    )

    assert isinstance(create_provider_client(mock_settings), MockProviderClient)
    assert isinstance(create_provider_client(groq_settings), GroqProviderClient)
    assert isinstance(create_provider_client(gemini_settings), GeminiProviderClient)


def test_groq_provider_parses_valid_decision_json(monkeypatch: pytest.MonkeyPatch) -> None:
    client = GroqProviderClient(api_key="test-key", model="llama-test")
    monkeypatch.setattr(
        client,
        "_post_chat_completion",
        lambda body: {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"recommendedAction":"renegotiate","confidenceScore":0.82,"rationale":"Low utilization supports renegotiation.",'
                            '"evidence":[{"factKey":"renewal_date","value":"2026-11-15","sourceDocumentId":"doc-email"}],'
                            '"projectedSavings":22560.0,"projectedSavingsStatus":"calculated","blockers":[],"nextStep":"Send the draft.",'
                            '"fallbackAction":"downgrade"}'
                        )
                    }
                }
            ]
        },
    )

    result = client.generate_json("DecisionAgent", "decision", _decision_payload())

    assert result["recommendedAction"] == "renegotiate"
    assert result["projectedSavings"] == 22560.0


def test_groq_provider_rejects_invalid_json_content(monkeypatch: pytest.MonkeyPatch) -> None:
    client = GroqProviderClient(api_key="test-key", model="llama-test")
    monkeypatch.setattr(
        client,
        "_post_chat_completion",
        lambda body: {"choices": [{"message": {"content": "not json"}}]},
    )

    with pytest.raises(ProviderResponseError):
        client.generate_json("DecisionAgent", "decision", _decision_payload())


def test_live_provider_decision_prompt_forbids_synthetic_evidence_sources() -> None:
    groq_client = GroqProviderClient(api_key="test-key", model="llama-test")
    gemini_client = GeminiProviderClient(api_key="test-key", model="gemini-test")

    groq_prompt = groq_client._build_messages("DecisionAgent", "decision", _decision_payload())[1]["content"]
    gemini_prompt = gemini_client._build_decision_prompt("decision", _decision_payload())

    assert "Never use synthetic sourceDocumentId values such as financeAnalysis" in groq_prompt
    assert "Never use synthetic sourceDocumentId values such as financeAnalysis" in gemini_prompt
    assert "Evidence must contain only the strongest 1 to 3 facts from documentAnalysis." in groq_prompt


def test_groq_provider_keeps_deterministic_agents_local(monkeypatch: pytest.MonkeyPatch) -> None:
    client = GroqProviderClient(api_key="test-key", model="llama-test")

    def _should_not_run(body):
        raise AssertionError("Groq HTTP path should not be used for deterministic agents.")

    monkeypatch.setattr(client, "_post_chat_completion", _should_not_run)
    result = client.generate_json(
        "FinanceAgent",
        "finance",
        {
            "documentAnalysis": {
                "facts": [
                    {"factKey": "seats_purchased", "value": 150},
                    {"factKey": "active_seats", "value": 28},
                    {"factKey": "annual_cost_usd", "value": 36000},
                ]
            }
        },
    )

    assert result["projectedSavingsStatus"] == "calculated"


def test_gemini_provider_parses_valid_decision_json(monkeypatch: pytest.MonkeyPatch) -> None:
    client = GeminiProviderClient(api_key="test-key", model="gemini-test")
    monkeypatch.setattr(
        client,
        "_post_generate_content",
        lambda body: {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": (
                                    '{"recommendedAction":"renegotiate","confidenceScore":0.82,"rationale":"Low utilization supports renegotiation.",'
                                    '"evidence":[{"factKey":"renewal_date","value":"2026-11-15","sourceDocumentId":"doc-email"}],'
                                    '"projectedSavings":22560.0,"projectedSavingsStatus":"calculated","blockers":[],"nextStep":"Send the draft.",'
                                    '"fallbackAction":"downgrade"}'
                                )
                            }
                        ]
                    }
                }
            ]
        },
    )

    result = client.generate_json("DecisionAgent", "decision", _decision_payload())

    assert result["recommendedAction"] == "renegotiate"
    assert result["projectedSavings"] == 22560.0


def test_gemini_provider_rejects_invalid_json_content(monkeypatch: pytest.MonkeyPatch) -> None:
    client = GeminiProviderClient(api_key="test-key", model="gemini-test")
    monkeypatch.setattr(
        client,
        "_post_generate_content",
        lambda body: {"candidates": [{"content": {"parts": [{"text": "not json"}]}}]},
    )

    with pytest.raises(ProviderResponseError):
        client.generate_json("DecisionAgent", "decision", _decision_payload())


def test_live_provider_comms_prompt_requires_distinct_artifact_styles() -> None:
    groq_client = GroqProviderClient(api_key="test-key", model="llama-test")
    gemini_client = GeminiProviderClient(api_key="test-key", model="gemini-test")

    groq_prompt = groq_client._build_messages(
        "CommsAgent",
        "artifact-generation",
        {
            "case": {"vendorName": "Golden Path Vendor"},
            "decision": {"recommendedAction": "renegotiate"},
            "documentAnalysis": {"facts": []},
        },
    )[1]["content"]
    gemini_prompt = gemini_client._build_comms_prompt(
        "artifact-generation",
        {
            "case": {"vendorName": "Golden Path Vendor"},
            "decision": {"recommendedAction": "renegotiate"},
            "documentAnalysis": {"facts": []},
        },
    )

    assert "cfo_summary: 2 to 3 sentences, executive tone" in groq_prompt
    assert "Do not repeat the same sentence structure across artifacts." in groq_prompt
    assert "vendor_email: 3 to 5 sentences, professional external tone" in gemini_prompt


def test_gemini_provider_keeps_deterministic_agents_local(monkeypatch: pytest.MonkeyPatch) -> None:
    client = GeminiProviderClient(api_key="test-key", model="gemini-test")

    def _should_not_run(body):
        raise AssertionError("Gemini HTTP path should not be used for deterministic agents.")

    monkeypatch.setattr(client, "_post_generate_content", _should_not_run)
    result = client.generate_json(
        "FinanceAgent",
        "finance",
        {
            "documentAnalysis": {
                "facts": [
                    {"factKey": "seats_purchased", "value": 150},
                    {"factKey": "active_seats", "value": 28},
                    {"factKey": "annual_cost_usd", "value": 36000},
                ]
            }
        },
    )

    assert result["projectedSavingsStatus"] == "calculated"


def test_decision_agent_rejects_inconsistent_llm_output() -> None:
    agent = DecisionAgent(
        StubProvider(
            {
                "recommendedAction": "renegotiate",
                "confidenceScore": 0.82,
                "rationale": "Low utilization supports renegotiation.",
                "evidence": [{"factKey": "renewal_date", "value": "2026-11-15", "sourceDocumentId": "doc-email"}],
                "projectedSavings": 99999,
                "projectedSavingsStatus": "calculated",
                "blockers": [],
                "nextStep": "Send the draft.",
                "fallbackAction": "downgrade",
            }
        )
    )

    with pytest.raises(AgentSchemaError):
        agent.run(_decision_payload())


def test_comms_agent_rejects_missing_required_artifacts() -> None:
    agent = CommsAgent(
        StubProvider(
            {
                "artifacts": [
                    {
                        "artifactType": ArtifactType.CFO_SUMMARY.value,
                        "title": "Summary",
                        "content": "Body",
                        "decisionVersion": 1,
                    }
                ]
            }
        )
    )

    with pytest.raises(AgentSchemaError):
        agent.run(
            {
                "case": {"vendorName": "Golden Path Vendor"},
                "decision": {
                    "recommendedAction": "renegotiate",
                    "confidenceScore": 0.82,
                    "rationale": "Low utilization supports renegotiation.",
                    "evidence": [],
                    "projectedSavings": 22560.0,
                    "projectedSavingsStatus": "calculated",
                    "blockers": [],
                    "nextStep": "Send the draft.",
                    "fallbackAction": "downgrade",
                },
                "document_analysis": {"facts": []},
            }
        )
