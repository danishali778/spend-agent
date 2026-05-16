import type { FactProvenanceKind, ProjectedSavingsStatus, RecommendedAction } from "./enums";

export interface DecisionEvidence {
  factKey: string;
  value: string | number | boolean | null;
  sourceDocumentId: string;
  sourceSnippet?: string;
  confidenceScore?: number;
  provenanceKind?: FactProvenanceKind;
}

export interface DecisionPacket {
  recommendedAction: RecommendedAction;
  confidenceScore: number;
  rationale: string;
  evidence: DecisionEvidence[];
  projectedSavings?: number | null;
  projectedSavingsStatus: ProjectedSavingsStatus;
  blockers: string[];
  nextStep: string;
  fallbackAction?: RecommendedAction | null;
}

export interface DecisionRecord {
  decisionVersion: number;
  decision: DecisionPacket;
}
