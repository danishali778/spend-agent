import type { CaseStatus, ProjectedSavingsStatus, RecommendedAction, RunFailureCategory, RunStatus } from "./enums";

export interface CaseSummary {
  id: string;
  vendorName: string;
  status: CaseStatus;
  renewalDate?: string | null;
  urgencyLevel?: string | null;
  projectedSavings?: number | null;
  projectedSavingsStatus: ProjectedSavingsStatus;
  recommendedAction?: RecommendedAction | null;
}

export interface CaseDetail extends CaseSummary {
  ownerUserId: string;
  notes?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface CaseRunState {
  latestRunId?: string | null;
  latestRunStatus?: RunStatus | null;
  latestRunFailureReason?: string | null;
  latestRunFailureCategory?: RunFailureCategory | null;
}

export interface CreateCaseInput {
  vendorName: string;
  ownerUserId: string;
  notes?: string;
  renewalDate?: string;
}
