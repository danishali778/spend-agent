import { AgentTimeline } from "../../../components/agent-timeline";
import { AnalyzeButton } from "../../../components/analyze-button";
import { ArtifactViewer } from "../../../components/artifact-viewer";
import { DecisionSummaryCard } from "../../../components/decision-summary-card";
import { DocumentList } from "../../../components/document-list";
import { DocumentUploadPanel } from "../../../components/document-upload-panel";
import { EvidencePanel } from "../../../components/evidence-panel";
import { RunStateCard } from "../../../components/run-state-card";
import { SavingsExplanationCard } from "../../../components/savings-explanation-card";
import { WorkflowStepper } from "../../../components/workflow-stepper";
import { getActivity, getArtifacts, getCase, getDecision } from "../../../lib/api-client";
import { formatCaseStatus, formatShortDate } from "../../../lib/presentation";

export default async function CaseDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [caseResponse, decisionResponse, artifactsResponse, activityResponse] = await Promise.all([
    getCase(id),
    getDecision(id),
    getArtifacts(id),
    getActivity(id)
  ]);

  return (
    <div className="stack-lg">
      {/* Header */}
      <div className="section-heading">
        <div className="stack-sm">
          <h1>{caseResponse.case.vendorName}</h1>
          <div className="row muted">
            <span className="pill">{formatCaseStatus(caseResponse.case.status)}</span>
            <span>Renewal: {formatShortDate(caseResponse.case.renewalDate)}</span>
          </div>
        </div>
        <AnalyzeButton caseId={id} />
      </div>

      {/* Stepper */}
      <WorkflowStepper 
        documents={caseResponse.documents}
        latestRunStatus={caseResponse.latestRunStatus}
        decision={decisionResponse?.decision ?? null}
        artifacts={artifactsResponse?.items ?? []}
        caseStatus={caseResponse.case.status}
      />

      {/* Two Column Layout */}
      <div className="case-detail-grid">
        {/* Main Workflow Column */}
        <div className="stack">
          <DecisionSummaryCard
            decision={decisionResponse?.decision ?? null}
            latestRunStatus={caseResponse.latestRunStatus}
            latestRunFailureReason={caseResponse.latestRunFailureReason}
            latestRunFailureCategory={caseResponse.latestRunFailureCategory}
            caseStatus={caseResponse.case.status}
          />
          <SavingsExplanationCard decision={decisionResponse?.decision ?? null} />
          <EvidencePanel evidence={decisionResponse?.decision.evidence ?? []} />
          <ArtifactViewer
            artifacts={artifactsResponse?.items ?? []}
            latestRunStatus={caseResponse.latestRunStatus}
            latestRunFailureCategory={caseResponse.latestRunFailureCategory}
          />
        </div>

        {/* Support Column */}
        <div className="stack">
          <RunStateCard caseResponse={caseResponse} activityResponse={activityResponse} />
          <DocumentUploadPanel caseId={id} documents={caseResponse.documents} />
          <DocumentList documents={caseResponse.documents} />
          <AgentTimeline
            events={activityResponse?.events ?? []}
            latestRunStatus={caseResponse.latestRunStatus}
            latestRunFailureCategory={caseResponse.latestRunFailureCategory}
            latestRunFailureReason={caseResponse.latestRunFailureReason}
          />
        </div>
      </div>
    </div>
  );
}
