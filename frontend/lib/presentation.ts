import type {
  AgentActivityEvent,
  ArtifactType,
  CaseStatus,
  DecisionEvidenceItem,
  DocumentType,
  ParseStatus,
  RecommendedAction,
  RunFailureCategory,
  RunStatus,
  StepStatus,
} from "@spendagent/shared-types";

const statusLabels: Record<CaseStatus, string> = {
  draft: "Draft",
  ingested: "Ingested",
  analyzing: "Analyzing",
  decision_ready: "Decision ready",
  needs_review: "Needs review",
  archived: "Archived",
};

const runStatusLabels: Record<RunStatus, string> = {
  queued: "Queued",
  running: "Running",
  completed: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
};

const stepStatusLabels: Record<StepStatus, string> = {
  pending: "Pending",
  running: "Running",
  completed: "Completed",
  failed: "Failed",
  skipped: "Skipped",
};

const actionLabels: Record<RecommendedAction, string> = {
  renew: "Renew",
  downgrade: "Downgrade",
  cancel: "Cancel",
  renegotiate: "Renegotiate",
  escalate: "Escalate",
};

const documentTypeLabels: Record<DocumentType, string> = {
  contract_pdf: "Contract PDF",
  invoice_pdf: "Invoice PDF",
  usage_csv: "Usage CSV",
  renewal_email: "Renewal email",
};

const parseStatusLabels: Record<ParseStatus, string> = {
  pending: "Pending",
  parsed: "Parsed",
  failed: "Failed",
};

const artifactTypeLabels: Record<ArtifactType, string> = {
  cfo_summary: "CFO summary",
  approval_note: "Approval note",
  vendor_email: "Vendor email",
};

const failureCategoryMessages: Record<RunFailureCategory, string> = {
  provider_unavailable: "The AI provider was unavailable during this run.",
  invalid_model_output: "The AI provider responded with an invalid structured output.",
  missing_critical_evidence: "Critical evidence was missing, so the run could not defend an autonomous decision.",
  finance_conflict: "The run detected conflicting finance evidence and routed the case for review.",
  parse_failure: "The uploaded evidence could not be parsed reliably.",
  unknown: "The latest run failed for an unknown reason.",
};

const agentLabels: Record<string, string> = {
  OrchestratorAgent: "Orchestrator",
  DocumentAgent: "Document analysis",
  FinanceAgent: "Finance analysis",
  PolicyAgent: "Policy check",
  DecisionAgent: "Decision",
  CommsAgent: "Artifact generation",
};

const stepLabels: Record<string, string> = {
  input_prep: "Input prep",
  document_analysis: "Document analysis",
  finance_analysis: "Finance analysis",
  policy_check: "Policy check",
  decision: "Decision",
  artifact_generation: "Artifact generation",
  persistence: "Persistence",
};

const factLabels: Record<string, string> = {
  renewal_date: "Renewal date",
  termination_notice_days: "Notice window",
  seats_purchased: "Purchased seats",
  annual_cost_usd: "Annual contract value",
  active_seats: "Active seats",
  utilization_percent: "Utilization",
  total_cost: "Total cost",
};

export function formatCaseStatus(value: CaseStatus): string {
  return statusLabels[value] ?? humanizeToken(value);
}

export function formatRunStatus(value: RunStatus): string {
  return runStatusLabels[value] ?? humanizeToken(value);
}

export function formatStepStatus(value: StepStatus): string {
  return stepStatusLabels[value] ?? humanizeToken(value);
}

export function formatRecommendedAction(value: RecommendedAction | null | undefined): string {
  if (!value) return "Pending";
  return actionLabels[value] ?? humanizeToken(value);
}

export function formatDocumentType(value: DocumentType): string {
  return documentTypeLabels[value] ?? humanizeToken(value);
}

export function formatParseStatus(value: ParseStatus): string {
  return parseStatusLabels[value] ?? humanizeToken(value);
}

export function formatArtifactType(value: ArtifactType): string {
  return artifactTypeLabels[value] ?? humanizeToken(value);
}

export function formatFailureCategory(value: RunFailureCategory | null | undefined): string | null {
  if (!value) return null;
  return failureCategoryMessages[value] ?? failureCategoryMessages.unknown;
}

export function formatAgentName(value: string): string {
  return agentLabels[value] ?? humanizeToken(value);
}

export function formatStepName(value: string): string {
  return stepLabels[value] ?? humanizeToken(value);
}

export function formatFactKey(value: string): string {
  return factLabels[value] ?? humanizeToken(value);
}

export function formatEvidenceValue(item: DecisionEvidenceItem): string | null {
  if (item.value == null) return null;
  if (typeof item.value === "number") {
    if (item.factKey.includes("cost") || item.factKey.includes("savings")) {
      return `$${item.value.toLocaleString()}`;
    }
    if (item.factKey.includes("percent")) {
      return `${item.value}%`;
    }
    return item.value.toLocaleString();
  }
  if (typeof item.value === "boolean") {
    return item.value ? "Yes" : "No";
  }
  return item.value;
}

export function formatConfidenceScore(value: number | null | undefined): string {
  if (value == null) return "Unknown";
  return `${Math.round(value * 100)}%`;
}

export function formatShortDate(value: string | null | undefined): string {
  if (!value) return "Unknown";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(date);
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "Unknown";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

export function formatEventTime(event: AgentActivityEvent): string | null {
  if (event.completedAt) return formatDateTime(event.completedAt);
  if (event.startedAt) return formatDateTime(event.startedAt);
  return null;
}

export function humanizeToken(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}
