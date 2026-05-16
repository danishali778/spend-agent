import { type UrgencyLevel } from "./urgency.ts";

export interface EscalationInput {
  missingCriticalFacts?: string[];
  conflicts?: string[];
  confidenceScore?: number | null;
  urgencyLevel?: UrgencyLevel | null;
  policyBlocked?: boolean;
}

export interface EscalationResult {
  shouldEscalate: boolean;
  blockers: string[];
  reasons: string[];
}

export function evaluateEscalation(input: EscalationInput): EscalationResult {
  const missingCriticalFacts = input.missingCriticalFacts ?? [];
  const conflicts = input.conflicts ?? [];
  const blockers = [...missingCriticalFacts, ...conflicts];
  const reasons: string[] = [];

  if (missingCriticalFacts.length > 0) {
    reasons.push("missing_critical_facts");
  }

  if (conflicts.length > 0) {
    reasons.push("conflicting_evidence");
  }

  if (input.policyBlocked) {
    reasons.push("policy_block");
  }

  if (input.confidenceScore != null && input.confidenceScore < 0.6) {
    reasons.push("low_confidence");
  }

  if (input.urgencyLevel === "critical" && blockers.length > 0) {
    reasons.push("critical_timing_with_blockers");
  }

  return {
    shouldEscalate: reasons.length > 0,
    blockers,
    reasons,
  };
}
