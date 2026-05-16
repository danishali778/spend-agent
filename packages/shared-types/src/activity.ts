import type { StepStatus } from "./enums";

export interface AgentActivityEvent {
  runId: string;
  agentName: string;
  stepName: string;
  status: StepStatus;
  startedAt?: string | null;
  completedAt?: string | null;
  summary?: string | null;
}

