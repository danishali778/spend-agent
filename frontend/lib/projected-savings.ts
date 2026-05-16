import type { CaseSummary, DecisionPacket, ProjectedSavingsStatus } from "@spendagent/shared-types";

type SavingsShape = Pick<CaseSummary, "projectedSavings" | "projectedSavingsStatus"> | Pick<DecisionPacket, "projectedSavings" | "projectedSavingsStatus">;

export function formatProjectedSavings(value: SavingsShape): string {
  if (value.projectedSavingsStatus === "calculated" && value.projectedSavings != null) {
    return `$${value.projectedSavings.toLocaleString()}`;
  }
  if (value.projectedSavingsStatus === "needs_spend_data") {
    return "Needs spend data";
  }
  return "N/A";
}

export function hasCalculatedProjectedSavings(status: ProjectedSavingsStatus, amount: number | null | undefined): amount is number {
  return status === "calculated" && amount != null;
}
