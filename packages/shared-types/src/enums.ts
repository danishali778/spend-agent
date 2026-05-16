export const CASE_STATUSES = [
  "draft",
  "ingested",
  "analyzing",
  "decision_ready",
  "needs_review",
  "archived",
] as const;

export const DOCUMENT_TYPES = [
  "contract_pdf",
  "invoice_pdf",
  "usage_csv",
  "renewal_email",
] as const;

export const RECOMMENDED_ACTIONS = [
  "renew",
  "downgrade",
  "cancel",
  "renegotiate",
  "escalate",
] as const;

export const RUN_STATUSES = [
  "queued",
  "running",
  "completed",
  "failed",
  "cancelled",
] as const;

export const STEP_STATUSES = [
  "pending",
  "running",
  "completed",
  "failed",
  "skipped",
] as const;

export const URGENCY_LEVELS = [
  "low",
  "medium",
  "high",
  "critical",
] as const;

export const PARSE_STATUSES = [
  "pending",
  "parsed",
  "failed",
] as const;

export const ARTIFACT_TYPES = [
  "cfo_summary",
  "approval_note",
  "vendor_email",
] as const;

export const POLICY_RESULTS = [
  "pass",
  "warn",
  "fail",
] as const;

export const PROJECTED_SAVINGS_STATUSES = [
  "calculated",
  "not_available",
  "needs_spend_data",
] as const;

export const FACT_PROVENANCE_KINDS = [
  "extracted",
  "inferred",
] as const;

export const RUN_FAILURE_CATEGORIES = [
  "provider_unavailable",
  "invalid_model_output",
  "missing_critical_evidence",
  "finance_conflict",
  "parse_failure",
  "unknown",
] as const;

export type CaseStatus = (typeof CASE_STATUSES)[number];
export type DocumentType = (typeof DOCUMENT_TYPES)[number];
export type RecommendedAction = (typeof RECOMMENDED_ACTIONS)[number];
export type RunStatus = (typeof RUN_STATUSES)[number];
export type StepStatus = (typeof STEP_STATUSES)[number];
export type UrgencyLevel = (typeof URGENCY_LEVELS)[number];
export type ParseStatus = (typeof PARSE_STATUSES)[number];
export type ArtifactType = (typeof ARTIFACT_TYPES)[number];
export type PolicyResult = (typeof POLICY_RESULTS)[number];
export type ProjectedSavingsStatus = (typeof PROJECTED_SAVINGS_STATUSES)[number];
export type FactProvenanceKind = (typeof FACT_PROVENANCE_KINDS)[number];
export type RunFailureCategory = (typeof RUN_FAILURE_CATEGORIES)[number];
