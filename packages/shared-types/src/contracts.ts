import type {
  ArtifactType,
  CaseStatus,
  DocumentType,
  ParseStatus,
  FactProvenanceKind,
  PolicyResult,
  ProjectedSavingsStatus,
  RecommendedAction,
  RunFailureCategory,
  RunStatus,
  StepStatus,
  UrgencyLevel,
} from "./enums.js";

export type PromptBundleVersion = `v${number}.${number}.${number}`;

export interface CaseSummary {
  id: string;
  vendorName: string;
  status: CaseStatus;
  renewalDate: string | null;
  urgencyLevel: UrgencyLevel | null;
  projectedSavings: number | null;
  projectedSavingsStatus: ProjectedSavingsStatus;
  recommendedAction: RecommendedAction | null;
}

export interface CaseDetail extends CaseSummary {
  ownerUserId: string;
  notes?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface CreateCaseInput {
  vendorName: string;
  ownerUserId: string;
  notes?: string;
  renewalDate?: string;
}

export interface DecisionEvidenceItem {
  factKey: string;
  value?: string | number | boolean | null;
  documentId: string;
  sourceName?: string | null;
  snippet: string;
  confidenceScore: number;
  provenanceKind?: FactProvenanceKind;
}

export interface DecisionBlocker {
  code: string;
  message: string;
}

export interface DecisionPacket {
  recommendedAction: RecommendedAction;
  confidenceScore: number;
  rationale: string;
  evidence: DecisionEvidenceItem[];
  projectedSavings: number | null;
  projectedSavingsStatus: ProjectedSavingsStatus;
  blockers: DecisionBlocker[];
  nextStep: string;
  fallbackAction: RecommendedAction | null;
}

export interface DecisionResponse {
  decisionVersion: number;
  decision: DecisionPacket;
}

export type GetDecisionResponse = DecisionResponse;

export interface GeneratedArtifact {
  artifactType: ArtifactType;
  title: string;
  content: string;
  decisionVersion: number;
  createdAt: string;
}

export interface DocumentSummary {
  id: string;
  type: DocumentType;
  sourceName: string;
  parseStatus: ParseStatus;
}

export interface AgentActivityEvent {
  runId: string;
  agentName: string;
  stepName: string;
  status: StepStatus;
  startedAt: string | null;
  completedAt: string | null;
  summary: string;
  error?: Record<string, unknown> | null;
}

export interface UploadEmailInput {
  type: "renewal_email";
  sourceName: string;
  emailText: string;
}

export interface AnalyzeCaseInput {
  forceReanalyze?: boolean;
}

export interface AnalyzeCaseResponse {
  runId: string;
  status: RunStatus;
}

export interface CreateCaseResponse {
  case: CaseSummary;
}

export interface ListCasesResponse {
  items: CaseSummary[];
  nextCursor: string | null;
}

export interface GetCaseResponse {
  case: CaseDetail;
  documents: DocumentSummary[];
  latestRunId: string | null;
  latestRunStatus?: RunStatus | null;
  latestRunFailureReason?: string | null;
  latestRunFailureCategory?: RunFailureCategory | null;
}

export interface GetArtifactsResponse {
  items: GeneratedArtifact[];
}

export interface GetActivityResponse {
  runId: string;
  status: RunStatus;
  events: AgentActivityEvent[];
  failureReason?: string | null;
  failureCategory?: RunFailureCategory | null;
}

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

export interface DocumentAgentFact {
  factKey: string;
  value: string | number | boolean | null;
  sourceDocumentId: string;
  sourceSnippet: string;
  confidenceScore: number;
  provenanceKind?: FactProvenanceKind;
  provenanceNote?: string | null;
}

export interface DocumentAgentOutput {
  facts: DocumentAgentFact[];
  ambiguities: string[];
  missingCriticalFacts: string[];
  missingSupportingFacts?: string[];
}

export interface SavingsScenario {
  action: RecommendedAction;
  projectedSavings: number | null;
  seatBaseline: number | null;
  rationale: string;
}

export interface UsageSnapshotResult {
  seatsPurchased: number | null;
  seatsActive: number | null;
  utilizationPercent: number | null;
  totalCost: number | null;
  costPeriod: "monthly" | "annual" | null;
  currency: string | null;
}

export interface FinanceAgentOutput {
  usageSnapshot: UsageSnapshotResult;
  savingsScenarios: SavingsScenario[];
  conflicts: string[];
}

export interface PolicyCheckResult {
  thresholdName: string;
  result: PolicyResult;
  message: string;
}

export interface PolicyAgentOutput {
  checks: PolicyCheckResult[];
  requiresEscalation: boolean;
}

export interface CommsArtifactDraft {
  artifactType: ArtifactType;
  title: string;
  content: string;
}

export interface CommsAgentOutput {
  artifacts: CommsArtifactDraft[];
}

export interface CaseRecord {
  id: string;
  vendor_name: string;
  owner_user_id: string;
  status: CaseStatus;
  renewal_date: string | null;
  urgency_level: UrgencyLevel | null;
  projected_savings: number | null;
  projected_savings_status: ProjectedSavingsStatus;
  recommended_action: RecommendedAction | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentRecord {
  id: string;
  case_id: string;
  type: DocumentType;
  source_name: string;
  storage_path: string | null;
  raw_text: string | null;
  mime_type: string | null;
  parse_status: ParseStatus;
  uploaded_at: string;
}

export interface ExtractedFactRecord {
  id: string;
  case_id: string;
  document_id: string;
  fact_key: string;
  fact_value_json: unknown;
  source_snippet: string | null;
  source_page: number | null;
  confidence_score: number;
  provenance_kind?: FactProvenanceKind;
  provenance_note?: string | null;
  extracted_by_run_id: string;
  created_at: string;
}

export interface UsageSnapshotRecord {
  id: string;
  case_id: string;
  seats_purchased: number | null;
  seats_active: number | null;
  utilization_percent: number | null;
  cost_period: "monthly" | "annual" | null;
  total_cost: number | null;
  currency: string;
  snapshot_source: "csv" | "invoice" | "merged";
  created_by_run_id: string;
  created_at: string;
}

export interface PolicyCheckRecord {
  id: string;
  case_id: string;
  run_id: string;
  proposed_action: RecommendedAction;
  threshold_name: string;
  result: PolicyResult;
  message: string;
  created_at: string;
}

export interface DecisionRecord {
  id: string;
  case_id: string;
  run_id: string;
  decision_version: number;
  recommended_action: RecommendedAction;
  fallback_action: RecommendedAction | null;
  confidence_score: number;
  rationale: string;
  projected_savings: number | null;
  projected_savings_status: ProjectedSavingsStatus;
  blockers_json: DecisionBlocker[];
  next_step: string;
  evidence_json: DecisionEvidenceItem[];
  created_at: string;
}

export interface GeneratedArtifactRecord {
  id: string;
  case_id: string;
  decision_id: string;
  artifact_type: ArtifactType;
  title: string;
  content: string;
  created_at: string;
}

export interface AgentRunRecord {
  id: string;
  case_id: string;
  status: RunStatus;
  triggered_by_user_id: string;
  started_at: string | null;
  completed_at: string | null;
  failure_reason: string | null;
  failure_category?: RunFailureCategory | null;
  prompt_bundle_version: PromptBundleVersion;
  created_at: string;
}

export interface AgentStepRecord {
  id: string;
  run_id: string;
  agent_name: string;
  step_name: string;
  status: StepStatus;
  summary: string | null;
  started_at: string | null;
  completed_at: string | null;
  retry_count: number;
  error_json: Record<string, unknown> | null;
}

export interface PublicSeedFixture {
  seedVersion: string;
  promptBundleVersion: PromptBundleVersion;
  caseSummary: CaseSummary;
  decisionPacket: DecisionPacket;
  generatedArtifacts: GeneratedArtifact[];
  activityTimeline: AgentActivityEvent[];
  db: {
    cases: CaseRecord[];
    documents: DocumentRecord[];
    extracted_facts: ExtractedFactRecord[];
    usage_snapshots: UsageSnapshotRecord[];
    policy_checks: PolicyCheckRecord[];
    decisions: DecisionRecord[];
    generated_artifacts: GeneratedArtifactRecord[];
    agent_runs: AgentRunRecord[];
    agent_steps: AgentStepRecord[];
  };
}
