export interface MetricCardViewModel {
  label: string;
  value: string;
  tone?: "default" | "warning" | "success";
}

export interface CaseTableRowViewModel {
  id: string;
  vendorName: string;
  status: string;
  urgencyLevel?: string | null;
  renewalDate?: string | null;
  projectedSavings?: number | null;
  recommendedAction?: string | null;
}

export interface TimelineEventViewModel {
  runId: string;
  agentName: string;
  stepName: string;
  status: string;
  summary?: string | null;
  startedAt?: string | null;
  completedAt?: string | null;
}

export interface EvidenceItemViewModel {
  factKey: string;
  value: string;
  sourceDocumentId: string;
}

export interface ArtifactViewModel {
  artifactType: string;
  title: string;
  content: string;
}

