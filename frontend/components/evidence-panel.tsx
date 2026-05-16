import type { DecisionEvidenceItem } from "@spendagent/shared-types";
import {
  formatConfidenceScore,
  formatEvidenceValue,
  formatFactKey,
} from "../lib/presentation";

function formatProvenance(value?: string | null) {
  if (value === "extracted") return "Extracted";
  if (value === "inferred") return "Inferred";
  return "Unspecified";
}

export function EvidencePanel({ evidence }: { evidence: DecisionEvidenceItem[] }) {
  if (evidence.length === 0) {
    return (
      <div className="card stack">
        <h3 className="panel-title">Supporting Evidence</h3>
        <p className="muted">No supporting evidence has been attached to the current decision.</p>
      </div>
    );
  }

  return (
    <div className="card stack">
      <div className="section-heading">
        <div className="stack-sm">
          <h3 className="panel-title">Supporting Evidence</h3>
          <p className="muted">Facts cited by the decision, with provenance and source snippets kept visible for review.</p>
        </div>
      </div>
      
      {evidence.map((item, index) => {
        const value = formatEvidenceValue(item);
        return (
          <div key={`${item.documentId}-${item.factKey}-${index}`} className="evidence-item stack-sm">
            <div className="evidence-row-header">
              <strong>{formatFactKey(item.factKey)}</strong>
              <span className="pill info">{formatProvenance(item.provenanceKind)}</span>
            </div>
            
            <div className="fact-strip compact">
              {value ? (
                <div>
                  <span className="field-label">Value</span>
                  <strong className="status-value">{value}</strong>
                </div>
              ) : null}
              <div>
                <span className="field-label">Source</span>
                <strong className="status-value word-break">{item.sourceName ?? item.documentId}</strong>
              </div>
              <div>
                <span className="field-label">Confidence</span>
                <strong className="status-value">{formatConfidenceScore(item.confidenceScore)}</strong>
              </div>
            </div>
            
            <blockquote className="muted blockquote-evidence">
              {item.snippet || "No source snippet available."}
            </blockquote>
          </div>
        );
      })}
    </div>
  );
}
