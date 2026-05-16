import type { DecisionPacket, RunFailureCategory, RunStatus } from "@spendagent/shared-types";
import { formatConfidenceScore, formatFailureCategory, formatRecommendedAction } from "../lib/presentation";
import { formatProjectedSavings } from "../lib/projected-savings";

export function DecisionSummaryCard({
  decision,
  latestRunStatus,
  latestRunFailureReason,
  latestRunFailureCategory,
  caseStatus,
}: {
  decision: DecisionPacket | null;
  latestRunStatus?: RunStatus | null;
  latestRunFailureReason?: string | null;
  latestRunFailureCategory?: RunFailureCategory | null;
  caseStatus?: string | null;
}) {
  if (!decision) {
    const failureMessage = formatFailureCategory(latestRunFailureCategory);
    return (
      <div className="card stack">
        <h2 className="panel-title">Recommendation</h2>
        <div className="alert info">
          <strong>{latestRunStatus === "failed" ? "Run Failed" : "Pending Analysis"}</strong>
          <p className="panel-copy">
            {latestRunStatus === "failed" 
              ? (failureMessage ?? "The latest analysis failed before a decision could be generated.") 
              : "Trigger analysis to generate a decision, savings estimate, and next-step guidance."}
          </p>
          {latestRunFailureReason ? <p className="panel-copy-tight">Detail: {latestRunFailureReason}</p> : null}
        </div>
      </div>
    );
  }

  // Determine recommendation styling based on review states
  let pillStyle = "success";
  let displayAction = formatRecommendedAction(decision.recommendedAction);
  const isNeedsReview = caseStatus === "needs_review";
  const isEscalate = decision.recommendedAction === "escalate";
  
  if (isNeedsReview || isEscalate || decision.blockers.length > 0) {
    pillStyle = "warning";
    if (isEscalate) pillStyle = "error";
  }

  // Determine confidence color (dynamic values allowed inline, but let's use the status classes or raw values if cleaner)
  let confidenceColor = "var(--success-text)";
  if (decision.confidenceScore < 0.6) confidenceColor = "var(--error-text)";
  else if (decision.confidenceScore < 0.8) confidenceColor = "var(--warning-text)";

  return (
    <div className="card stack">
      <div className="section-heading">
        <h2 className="panel-title">Recommendation</h2>
        <span className={`pill ${pillStyle} status-value`}>
          {displayAction}
        </span>
      </div>

      {(isNeedsReview || isEscalate) && (
        <div className={`alert ${pillStyle}`}>
          <strong>Human Review Required</strong>
          <p className="panel-copy">
            {isEscalate ? "This recommendation requires escalation for manual review." : "This case has been flagged for human review before any autonomous action."}
          </p>
        </div>
      )}

      <div className="metric-strip metric-strip-compact">
        <div className="stack-sm">
          <span className="field-label">Confidence</span>
          <strong className="metric-value" style={{ color: confidenceColor }}>
            {formatConfidenceScore(decision.confidenceScore)}
          </strong>
        </div>
        <div className="stack-sm">
          <span className="field-label">Projected Savings</span>
          <strong className="metric-value">
            {formatProjectedSavings(decision)}
          </strong>
        </div>
      </div>

      {decision.blockers.length > 0 && (
        <div className="alert error">
          <strong>Review Blockers</strong>
          <ul className="panel-copy">
            {decision.blockers.map((blocker, i) => (
              <li key={i}>{blocker.message}</li>
            ))}
          </ul>
        </div>
      )}

      <div>
        <span className="field-label">Rationale</span>
        <p className="panel-copy">{decision.rationale}</p>
      </div>

      <div className="panel-subtle">
        <span className="field-label">Next Step</span>
        <p className="panel-copy">{decision.nextStep}</p>
      </div>
    </div>
  );
}
