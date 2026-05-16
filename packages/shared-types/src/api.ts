import type { AgentActivityEvent } from "./activity";
import type { GeneratedArtifact } from "./artifact";
import type { CaseDetail, CaseSummary, CreateCaseInput } from "./case";
import type { DecisionRecord } from "./decision";
import type { DocumentSummary, UploadEmailInput } from "./document";
import type { RunStatus } from "./enums";

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
  latestRunId?: string | null;
}

export interface AnalyzeCaseInput {
  forceReanalyze?: boolean;
}

export interface AnalyzeCaseResponse {
  runId: string;
  status: RunStatus;
}

export interface GetDecisionResponse extends DecisionRecord {}

export interface GetArtifactsResponse {
  items: GeneratedArtifact[];
}

export interface GetActivityResponse {
  runId: string;
  status: RunStatus;
  events: AgentActivityEvent[];
}

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

export type CaseApi =
  | CreateCaseInput
  | CreateCaseResponse
  | ListCasesResponse
  | GetCaseResponse
  | AnalyzeCaseInput
  | AnalyzeCaseResponse
  | GetDecisionResponse
  | GetArtifactsResponse
  | GetActivityResponse
  | UploadEmailInput
  | ApiErrorResponse;

