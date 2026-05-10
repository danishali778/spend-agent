from __future__ import annotations

from pydantic import BaseModel, Field


class CaseSummary(BaseModel):
    id: str
    vendorName: str
    status: str
    renewalDate: str | None = None
    urgencyLevel: str | None = None
    projectedSavings: float | None = None
    projectedSavingsStatus: str
    recommendedAction: str | None = None


class CaseDetail(CaseSummary):
    ownerUserId: str
    notes: str | None = None
    createdAt: str
    updatedAt: str


class CreateCaseInput(BaseModel):
    vendorName: str
    ownerUserId: str
    notes: str | None = None
    renewalDate: str | None = None


class DecisionEvidenceItem(BaseModel):
    factKey: str
    value: str | int | float | bool | None = None
    documentId: str
    sourceName: str | None = None
    snippet: str
    confidenceScore: float
    provenanceKind: str | None = None


class DecisionBlocker(BaseModel):
    code: str
    message: str


class DecisionPacketResponse(BaseModel):
    recommendedAction: str
    confidenceScore: float
    rationale: str
    evidence: list[DecisionEvidenceItem]
    projectedSavings: float | None = None
    projectedSavingsStatus: str
    blockers: list[DecisionBlocker]
    nextStep: str
    fallbackAction: str | None = None


class DecisionResponse(BaseModel):
    decisionVersion: int
    decision: DecisionPacketResponse


class GeneratedArtifactResponse(BaseModel):
    artifactType: str
    title: str
    content: str
    decisionVersion: int
    createdAt: str | None = None


class DocumentSummary(BaseModel):
    id: str
    type: str
    sourceName: str
    parseStatus: str


class AgentActivityEventResponse(BaseModel):
    runId: str
    agentName: str
    stepName: str
    status: str
    startedAt: str | None = None
    completedAt: str | None = None
    summary: str = ""
    error: dict | None = None


class UploadEmailInput(BaseModel):
    type: str = Field(pattern="^renewal_email$")
    sourceName: str
    emailText: str


class AnalyzeCaseInput(BaseModel):
    forceReanalyze: bool | None = None


class AnalyzeCaseResponse(BaseModel):
    runId: str
    status: str


class CreateCaseResponse(BaseModel):
    case: CaseSummary


class ListCasesResponse(BaseModel):
    items: list[CaseSummary]
    nextCursor: str | None = None


class GetCaseResponse(BaseModel):
    case: CaseDetail
    documents: list[DocumentSummary]
    latestRunId: str | None = None
    latestRunStatus: str | None = None
    latestRunFailureReason: str | None = None
    latestRunFailureCategory: str | None = None


class GetArtifactsResponse(BaseModel):
    items: list[GeneratedArtifactResponse]


class GetActivityResponse(BaseModel):
    runId: str
    status: str
    events: list[AgentActivityEventResponse]
    failureReason: str | None = None
    failureCategory: str | None = None
