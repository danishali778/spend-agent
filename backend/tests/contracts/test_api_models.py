from __future__ import annotations

from app.schemas.api import (
    AgentActivityEventResponse,
    AnalyzeCaseResponse,
    CaseDetail,
    CaseSummary,
    DecisionBlocker,
    DecisionEvidenceItem,
    DecisionPacketResponse,
    DecisionResponse,
    DocumentSummary,
    GetActivityResponse,
    GetArtifactsResponse,
    GetCaseResponse,
    GeneratedArtifactResponse,
    ListCasesResponse,
)


def test_case_list_contract_uses_frontend_field_names() -> None:
    response = ListCasesResponse(
        items=[
            CaseSummary(
                id="case-1",
                vendorName="Alpha CRM",
                status="draft",
                renewalDate=None,
                urgencyLevel=None,
                projectedSavings=None,
                projectedSavingsStatus="not_available",
                recommendedAction=None,
            )
        ],
        nextCursor=None,
    )

    payload = response.model_dump()
    assert set(payload.keys()) == {"items", "nextCursor"}
    assert set(payload["items"][0].keys()) == {
        "id",
        "vendorName",
        "status",
        "renewalDate",
        "urgencyLevel",
        "projectedSavings",
        "projectedSavingsStatus",
        "recommendedAction",
    }


def test_case_detail_contract_includes_documents_and_latest_run() -> None:
    response = GetCaseResponse(
        case=CaseDetail(
            id="case-1",
            vendorName="Alpha CRM",
            status="draft",
            renewalDate=None,
            urgencyLevel=None,
            projectedSavings=None,
            projectedSavingsStatus="not_available",
            recommendedAction=None,
            ownerUserId="user-1",
            notes=None,
            createdAt="2026-05-08T00:00:00+00:00",
            updatedAt="2026-05-08T00:00:00+00:00",
        ),
        documents=[
            DocumentSummary(
                id="doc-1",
                type="renewal_email",
                sourceName="renewal-reminder",
                parseStatus="parsed",
            )
        ],
        latestRunId="run-1",
        latestRunStatus="completed",
        latestRunFailureReason=None,
        latestRunFailureCategory=None,
    )

    payload = response.model_dump()
    assert set(payload.keys()) == {"case", "documents", "latestRunId", "latestRunStatus", "latestRunFailureReason", "latestRunFailureCategory"}
    assert payload["documents"][0]["parseStatus"] == "parsed"


def test_decision_artifact_and_activity_contracts_match_expected_envelopes() -> None:
    decision = DecisionResponse(
        decisionVersion=1,
        decision=DecisionPacketResponse(
            recommendedAction="renegotiate",
            confidenceScore=0.82,
            rationale="Low utilization supports a renegotiation recommendation.",
            evidence=[
                DecisionEvidenceItem(
                    factKey="renewal_date",
                    value="2026-07-01",
                    documentId="doc-1",
                    sourceName="renewal-reminder",
                    snippet="Renews on 2026-07-01",
                    confidenceScore=0.94,
                    provenanceKind="extracted",
                )
            ],
            projectedSavings=18240.0,
            projectedSavingsStatus="calculated",
            blockers=[DecisionBlocker(code="notice_window", message="Notice window is closing soon.")],
            nextStep="Send the negotiation draft.",
            fallbackAction="downgrade",
        ),
    )
    artifacts = GetArtifactsResponse(
        items=[
            GeneratedArtifactResponse(
                artifactType="cfo_summary",
                title="Renewal Recommendation",
                content="Memo",
                decisionVersion=1,
                createdAt="2026-05-08T00:00:00+00:00",
            )
        ]
    )
    activity = GetActivityResponse(
        runId="run-1",
        status="completed",
        events=[
            AgentActivityEventResponse(
                runId="run-1",
                agentName="DocumentAgent",
                stepName="document_analysis",
                status="completed",
                startedAt="2026-05-08T00:00:00+00:00",
                completedAt="2026-05-08T00:00:03+00:00",
                summary="Extracted contract facts.",
                error=None,
            )
        ],
        failureReason=None,
        failureCategory=None,
    )

    assert decision.model_dump()["decision"]["recommendedAction"] == "renegotiate"
    assert artifacts.model_dump()["items"][0]["artifactType"] == "cfo_summary"
    assert activity.model_dump()["events"][0]["agentName"] == "DocumentAgent"


def test_analyze_contract_preserves_run_id_and_status() -> None:
    response = AnalyzeCaseResponse(runId="run-1", status="queued")
    assert response.model_dump() == {"runId": "run-1", "status": "queued"}
