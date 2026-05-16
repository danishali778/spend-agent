import { CaseStatus, DecisionPacket, DocumentSummary, GeneratedArtifact, RunStatus } from "@spendagent/shared-types";

export function WorkflowStepper({
  documents,
  latestRunStatus,
  decision,
  artifacts,
  caseStatus
}: {
  documents: DocumentSummary[];
  latestRunStatus?: RunStatus | null;
  decision: DecisionPacket | null;
  artifacts: GeneratedArtifact[];
  caseStatus: CaseStatus;
}) {
  const hasDocuments = documents.length > 0;
  const isRunning = latestRunStatus === "running";
  const hasDecision = decision !== null;
  const hasArtifacts = artifacts.length > 0;
  
  // Evidence
  const stepEvidence = hasDocuments ? "completed" : "active";
  
  // Analysis
  let stepAnalysis = "pending";
  if (isRunning) stepAnalysis = "active";
  if (hasDecision || latestRunStatus === "completed") stepAnalysis = "completed";
  if (latestRunStatus === "failed") stepAnalysis = "error";
  
  // Recommendation
  let stepRecommendation = "pending";
  if (latestRunStatus === "failed" && !hasDecision) {
    stepRecommendation = "error";
  } else if (hasDecision) {
    const needsReview = caseStatus === "needs_review" || decision.recommendedAction === "escalate" || decision.blockers.length > 0;
    if (needsReview) stepRecommendation = "warning-active";
    else stepRecommendation = "completed";
  }

  // Artifacts
  let stepArtifacts = "pending";
  if (latestRunStatus === "failed" && !hasArtifacts) {
    stepArtifacts = "error";
  } else if (hasDecision && !hasArtifacts) {
    stepArtifacts = "active";
  } else if (hasArtifacts) {
    stepArtifacts = "completed";
  }

  const steps = [
    { label: "Evidence", status: stepEvidence },
    { label: "Analysis", status: stepAnalysis },
    { label: "Recommendation", status: stepRecommendation },
    { label: "Artifacts", status: stepArtifacts }
  ];

  return (
    <div className="workflow-stepper">
      {steps.map((step, index) => {
        let icon = null;
        if (step.status === "completed") icon = <span className="workflow-icon success">✓</span>;
        if (step.status === "error") icon = <span className="workflow-icon error">!</span>;
        if (step.label === "Recommendation" && step.status === "warning-active") icon = <span className="workflow-icon warning">!</span>;

        return (
          <div key={step.label} className="workflow-step">
            <div className={`step-item ${step.status}`}>
              {icon}
              {step.label}
            </div>
            {index < steps.length - 1 && <div className="step-divider">—</div>}
          </div>
        );
      })}
    </div>
  );
}
