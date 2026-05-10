from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict


class DocumentType(str, Enum):
    CONTRACT_PDF = "contract_pdf"
    INVOICE_PDF = "invoice_pdf"
    USAGE_CSV = "usage_csv"
    RENEWAL_EMAIL = "renewal_email"


class RecommendedAction(str, Enum):
    RENEW = "renew"
    DOWNGRADE = "downgrade"
    CANCEL = "cancel"
    RENEGOTIATE = "renegotiate"
    ESCALATE = "escalate"


class ProjectedSavingsStatus(str, Enum):
    CALCULATED = "calculated"
    NOT_AVAILABLE = "not_available"
    NEEDS_SPEND_DATA = "needs_spend_data"


class FactProvenanceKind(str, Enum):
    EXTRACTED = "extracted"
    INFERRED = "inferred"


class RunFailureCategory(str, Enum):
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    INVALID_MODEL_OUTPUT = "invalid_model_output"
    MISSING_CRITICAL_EVIDENCE = "missing_critical_evidence"
    FINANCE_CONFLICT = "finance_conflict"
    PARSE_FAILURE = "parse_failure"
    UNKNOWN = "unknown"


class ArtifactType(str, Enum):
    CFO_SUMMARY = "cfo_summary"
    APPROVAL_NOTE = "approval_note"
    VENDOR_EMAIL = "vendor_email"


class PageText(BaseModel):
    page_number: int
    text: str


class PdfExtractionResult(BaseModel):
    status: str
    text: str
    pages: list[PageText] = []
    error_code: str | None = None
    message: str | None = None


class ClauseMatch(BaseModel):
    label: str
    snippet: str
    start: int
    end: int


class MoneyAmount(BaseModel):
    currency: str | None
    amount: float
    raw: str


class EmailFieldsResult(BaseModel):
    status: str
    subject: str | None
    sender: str | None
    body: str
    detected_dates: list[str] = []
    error_code: str | None = None
    message: str | None = None


class UsageRow(BaseModel):
    user_id: str
    active: bool
    last_seen_at: str | None
    raw: dict[str, Any]


class UsageSummary(BaseModel):
    active_users: int
    total_rows: int
    inactive_users: int


class UsageNormalizationResult(BaseModel):
    status: str
    rows: list[UsageRow] = []
    summary: UsageSummary | None = None
    error_code: str | None = None
    message: str | None = None


class CaseRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    vendor_name: str
    owner_user_id: str
    status: str = "draft"
    renewal_date: str | None = None
    urgency_level: str | None = None
    projected_savings: float | None = None
    projected_savings_status: ProjectedSavingsStatus = ProjectedSavingsStatus.NOT_AVAILABLE
    recommended_action: RecommendedAction | None = None

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "vendorName": self.vendor_name,
            "ownerUserId": self.owner_user_id,
            "status": self.status,
            "renewalDate": self.renewal_date,
            "urgencyLevel": self.urgency_level,
            "projectedSavings": self.projected_savings,
            "projectedSavingsStatus": self.projected_savings_status.value,
            "recommendedAction": self.recommended_action.value if self.recommended_action else None,
        }


class DocumentRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    case_id: str
    type: DocumentType
    source_name: str
    raw_text: str | None = None
    parse_status: str = "pending"
    storage_path: str | None = None
    mime_type: str | None = None

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "caseId": self.case_id,
            "type": self.type.value,
            "sourceName": self.source_name,
            "rawText": self.raw_text,
            "parseStatus": self.parse_status,
            "storagePath": self.storage_path,
            "mimeType": self.mime_type,
        }


class ExtractedFact(BaseModel):
    fact_key: str
    value: Any
    source_document_id: str
    source_snippet: str
    confidence_score: float
    provenance_kind: FactProvenanceKind = FactProvenanceKind.EXTRACTED
    provenance_note: str | None = None

    @classmethod
    def from_agent_dict(cls, data: dict[str, Any]) -> "ExtractedFact":
        return cls(
            fact_key=str(data["factKey"]),
            value=data["value"],
            source_document_id=str(data["sourceDocumentId"]),
            source_snippet=str(data["sourceSnippet"]),
            confidence_score=float(data["confidenceScore"]),
            provenance_kind=FactProvenanceKind(str(data.get("provenanceKind", "extracted"))),
            provenance_note=data.get("provenanceNote"),
        )

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "factKey": self.fact_key,
            "value": self.value,
            "sourceDocumentId": self.source_document_id,
            "sourceSnippet": self.source_snippet,
            "confidenceScore": self.confidence_score,
            "provenanceKind": self.provenance_kind.value,
            "provenanceNote": self.provenance_note,
        }


class DocumentAnalysisResult(BaseModel):
    facts: list[ExtractedFact]
    ambiguities: list[str]
    missing_critical_facts: list[str]
    missing_supporting_facts: list[str] = []

    @classmethod
    def from_agent_dict(cls, data: dict[str, Any]) -> "DocumentAnalysisResult":
        return cls(
            facts=[ExtractedFact.from_agent_dict(item) for item in data["facts"]],
            ambiguities=[str(item) for item in data.get("ambiguities", [])],
            missing_critical_facts=[str(item) for item in data.get("missingCriticalFacts", [])],
            missing_supporting_facts=[str(item) for item in data.get("missingSupportingFacts", [])],
        )

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "facts": [fact.to_state_dict() for fact in self.facts],
            "ambiguities": self.ambiguities,
            "missingCriticalFacts": self.missing_critical_facts,
            "missingSupportingFacts": self.missing_supporting_facts,
        }


class UsageSnapshot(BaseModel):
    seats_purchased: int | None
    seats_active: int | None
    utilization_percent: float | None
    total_cost: float | None
    cost_period: str | None
    currency: str | None

    @classmethod
    def from_agent_dict(cls, data: dict[str, Any]) -> "UsageSnapshot":
        return cls(
            seats_purchased=data.get("seatsPurchased"),
            seats_active=data.get("seatsActive"),
            utilization_percent=data.get("utilizationPercent"),
            total_cost=data.get("totalCost"),
            cost_period=data.get("costPeriod"),
            currency=data.get("currency"),
        )

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "seatsPurchased": self.seats_purchased,
            "seatsActive": self.seats_active,
            "utilizationPercent": self.utilization_percent,
            "totalCost": self.total_cost,
            "costPeriod": self.cost_period,
            "currency": self.currency,
        }


class SavingsScenario(BaseModel):
    action: RecommendedAction
    projected_savings: float | None
    projected_savings_status: ProjectedSavingsStatus
    summary: str

    @classmethod
    def from_agent_dict(cls, data: dict[str, Any]) -> "SavingsScenario":
        return cls(
            action=RecommendedAction(str(data["action"])),
            projected_savings=data.get("projectedSavings"),
            projected_savings_status=ProjectedSavingsStatus(str(data.get("projectedSavingsStatus", "not_available"))),
            summary=str(data["summary"]),
        )

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.value,
            "projectedSavings": self.projected_savings,
            "projectedSavingsStatus": self.projected_savings_status.value,
            "summary": self.summary,
        }


class FinanceAnalysisResult(BaseModel):
    usage_snapshot: UsageSnapshot
    savings_scenarios: list[SavingsScenario]
    projected_savings_status: ProjectedSavingsStatus = ProjectedSavingsStatus.NOT_AVAILABLE
    conflicts: list[str]

    @classmethod
    def from_agent_dict(cls, data: dict[str, Any]) -> "FinanceAnalysisResult":
        return cls(
            usage_snapshot=UsageSnapshot.from_agent_dict(data["usageSnapshot"]),
            savings_scenarios=[SavingsScenario.from_agent_dict(item) for item in data.get("savingsScenarios", [])],
            projected_savings_status=ProjectedSavingsStatus(str(data.get("projectedSavingsStatus", "not_available"))),
            conflicts=[str(item) for item in data.get("conflicts", [])],
        )

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "usageSnapshot": self.usage_snapshot.to_state_dict(),
            "savingsScenarios": [item.to_state_dict() for item in self.savings_scenarios],
            "projectedSavingsStatus": self.projected_savings_status.value,
            "conflicts": self.conflicts,
        }


class PolicyCheckResult(BaseModel):
    threshold_name: str
    result: str
    message: str

    @classmethod
    def from_agent_dict(cls, data: dict[str, Any]) -> "PolicyCheckResult":
        return cls(
            threshold_name=str(data["thresholdName"]),
            result=str(data["result"]),
            message=str(data["message"]),
        )

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "thresholdName": self.threshold_name,
            "result": self.result,
            "message": self.message,
        }


class PolicyEvaluationResult(BaseModel):
    checks: list[PolicyCheckResult]
    requires_escalation: bool

    @classmethod
    def from_agent_dict(cls, data: dict[str, Any]) -> "PolicyEvaluationResult":
        return cls(
            checks=[PolicyCheckResult.from_agent_dict(item) for item in data.get("checks", [])],
            requires_escalation=bool(data["requiresEscalation"]),
        )

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "checks": [item.to_state_dict() for item in self.checks],
            "requiresEscalation": self.requires_escalation,
        }


class EvidenceItem(BaseModel):
    fact_key: str
    value: Any
    source_document_id: str
    source_snippet: str = ""
    confidence_score: float = 0
    provenance_kind: FactProvenanceKind = FactProvenanceKind.EXTRACTED

    @classmethod
    def from_agent_dict(cls, data: dict[str, Any]) -> "EvidenceItem":
        return cls(
            fact_key=str(data["factKey"]),
            value=data.get("value"),
            source_document_id=str(data["sourceDocumentId"]),
            source_snippet=str(data.get("sourceSnippet", "")),
            confidence_score=float(data.get("confidenceScore") or 0),
            provenance_kind=FactProvenanceKind(str(data.get("provenanceKind", "extracted"))),
        )

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "factKey": self.fact_key,
            "value": self.value,
            "sourceDocumentId": self.source_document_id,
            "sourceSnippet": self.source_snippet,
            "confidenceScore": self.confidence_score,
            "provenanceKind": self.provenance_kind.value,
        }


class DecisionPacket(BaseModel):
    recommended_action: RecommendedAction
    confidence_score: float
    rationale: str
    evidence: list[EvidenceItem]
    projected_savings: float | None
    projected_savings_status: ProjectedSavingsStatus
    blockers: list[str]
    next_step: str
    fallback_action: RecommendedAction | None

    @classmethod
    def from_agent_dict(cls, data: dict[str, Any]) -> "DecisionPacket":
        fallback = data.get("fallbackAction")
        return cls(
            recommended_action=RecommendedAction(str(data["recommendedAction"])),
            confidence_score=float(data["confidenceScore"]),
            rationale=str(data["rationale"]),
            evidence=[EvidenceItem.from_agent_dict(item) for item in data.get("evidence", [])],
            projected_savings=data.get("projectedSavings"),
            projected_savings_status=ProjectedSavingsStatus(str(data.get("projectedSavingsStatus", "not_available"))),
            blockers=[str(item) for item in data.get("blockers", [])],
            next_step=str(data["nextStep"]),
            fallback_action=None if fallback in (None, "") else RecommendedAction(str(fallback)),
        )

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "recommendedAction": self.recommended_action.value,
            "confidenceScore": self.confidence_score,
            "rationale": self.rationale,
            "evidence": [item.to_state_dict() for item in self.evidence],
            "projectedSavings": self.projected_savings,
            "projectedSavingsStatus": self.projected_savings_status.value,
            "blockers": self.blockers,
            "nextStep": self.next_step,
            "fallbackAction": self.fallback_action.value if self.fallback_action else None,
        }


class GeneratedArtifact(BaseModel):
    artifact_type: ArtifactType
    title: str
    content: str
    decision_version: int = 1
    created_at: str | None = None

    @classmethod
    def from_agent_dict(cls, data: dict[str, Any]) -> "GeneratedArtifact":
        return cls(
            artifact_type=ArtifactType(str(data["artifactType"])),
            title=str(data["title"]),
            content=str(data["content"]),
            decision_version=int(data.get("decisionVersion", 1)),
            created_at=data.get("createdAt"),
        )

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "artifactType": self.artifact_type.value,
            "title": self.title,
            "content": self.content,
            "decisionVersion": self.decision_version,
            "createdAt": self.created_at,
        }


class CommsAgentResult(BaseModel):
    artifacts: list[GeneratedArtifact]

    @classmethod
    def from_agent_dict(cls, data: dict[str, Any]) -> "CommsAgentResult":
        return cls(artifacts=[GeneratedArtifact.from_agent_dict(item) for item in data["artifacts"]])

    def to_state_dict(self) -> dict[str, Any]:
        return {"artifacts": [item.to_state_dict() for item in self.artifacts]}


class AgentActivityEvent(BaseModel):
    run_id: str
    agent_name: str
    step_name: str
    status: str
    started_at: str | None
    completed_at: str | None
    summary: str | None
    retry_count: int = 0
    error: dict[str, Any] | None = None

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "runId": self.run_id,
            "agentName": self.agent_name,
            "stepName": self.step_name,
            "status": self.status,
            "startedAt": self.started_at,
            "completedAt": self.completed_at,
            "summary": self.summary,
            "retryCount": self.retry_count,
            "error": self.error,
        }
