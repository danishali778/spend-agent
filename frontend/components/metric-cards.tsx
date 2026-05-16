import type { CaseSummary } from "@spendagent/shared-types";
import { hasCalculatedProjectedSavings } from "../lib/projected-savings";

export function MetricCards({ items }: { items: CaseSummary[] }) {
  const calculatedSavings = items.filter((item) => hasCalculatedProjectedSavings(item.projectedSavingsStatus, item.projectedSavings));
  const projectedSavings = calculatedSavings.reduce((total, item) => total + (item.projectedSavings ?? 0), 0);
  const activeCases = items.length;
  const decisionReady = items.filter((item) => item.status === "decision_ready").length;
  const needsReview = items.filter((item) => item.status === "needs_review").length;

  return (
    <div className="metric-strip">
      <div className="card stack-sm">
        <span className="field-label">Active cases</span>
        <div className="metric-value">{activeCases}</div>
      </div>
      <div className="card stack-sm">
        <span className="field-label">Decision ready</span>
        <div className="metric-value">{decisionReady}</div>
      </div>
      <div className="card stack-sm">
        <span className="field-label">Projected savings</span>
        <div className="metric-value">
          {calculatedSavings.length > 0 ? `$${projectedSavings.toLocaleString()}` : "N/A"}
        </div>
      </div>
      <div className="card stack-sm">
        <span className="field-label">Needs review</span>
        <div className="metric-value">{needsReview}</div>
      </div>
    </div>
  );
}
