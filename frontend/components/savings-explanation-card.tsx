import type { DecisionEvidenceItem, DecisionPacket } from "@spendagent/shared-types";
import { formatEvidenceValue, formatFactKey, formatRecommendedAction } from "../lib/presentation";
import { formatProjectedSavings } from "../lib/projected-savings";

function findEvidence(evidence: DecisionEvidenceItem[], factKey: string): DecisionEvidenceItem | undefined {
  return evidence.find((item) => item.factKey === factKey);
}

export function SavingsExplanationCard({ decision }: { decision: DecisionPacket | null }) {
  if (!decision) {
    return (
      <section className="card stack">
        <div className="section-heading">
          <h3 className="panel-title">Savings Logic</h3>
        </div>
        <p className="muted">Run analysis to see how SpendAgent connects utilization, contract value, and the recommended action.</p>
      </section>
    );
  }

  const purchasedSeats = findEvidence(decision.evidence, "seats_purchased");
  const activeSeats = findEvidence(decision.evidence, "active_seats");
  const annualCost = findEvidence(decision.evidence, "annual_cost_usd");
  const hasSeatMath = purchasedSeats?.value != null && activeSeats?.value != null;
  const hasCalculatedSavings = decision.projectedSavingsStatus === "calculated" && decision.projectedSavings != null;

  return (
    <section className="card stack">
      <div className="section-heading">
        <div className="stack-sm">
          <h3 className="panel-title">Savings Logic</h3>
          <p className="muted">The recommendation is anchored to the strongest available facts.</p>
        </div>
        <span className="pill info">{formatRecommendedAction(decision.fallbackAction)} (Fallback)</span>
      </div>

      <div className="reasoning-box">
        {hasCalculatedSavings ? (
          <p className="panel-copy">
            SpendAgent found enough spend and seat evidence to estimate avoidable annual cost. The current logic keeps a buffer above active seats, then compares that target against the purchased-seat baseline.
          </p>
        ) : decision.projectedSavingsStatus === "needs_spend_data" ? (
          <p className="panel-copy">
            Seat usage supports a renewal discussion, but annual spend evidence is missing. Upload an invoice or contract value to convert the usage gap into a dollar estimate.
          </p>
        ) : (
          <p className="panel-copy" style={{ color: "var(--warning-text)" }}>
            The run did not have enough reliable spend and usage evidence to calculate savings defensibly.
          </p>
        )}
      </div>

      {hasSeatMath || annualCost ? (
        <div className="fact-strip compact">
          {[purchasedSeats, activeSeats, annualCost].filter(Boolean).map((item) => (
            <div key={item!.factKey}>
              <span className="eyebrow">{formatFactKey(item!.factKey)}</span>
              <strong className="metric-value">{formatEvidenceValue(item!)}</strong>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
