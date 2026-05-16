import type { GetActivityResponse, GetCaseResponse } from "@spendagent/shared-types";
import { formatCaseStatus, formatDateTime, formatFailureCategory, formatRunStatus, formatShortDate } from "../lib/presentation";

export function RunStateCard({
  caseResponse,
  activityResponse,
}: {
  caseResponse: GetCaseResponse;
  activityResponse: GetActivityResponse | null;
}) {
  const latestRunStatus = caseResponse.latestRunStatus;
  const failureCategoryMessage = formatFailureCategory(caseResponse.latestRunFailureCategory);
  const failureReason = caseResponse.latestRunFailureReason ?? activityResponse?.failureReason ?? null;
  const isNeedsReview = caseResponse.case.status === "needs_review" && latestRunStatus !== "failed";

  return (
    <div className="card stack-sm">
      <h3 className="panel-title">Current Status</h3>
      
      <div className="detail-row detail-row-spaced">
        <span className="field-label">Case Status</span>
        <span className="status-value">{formatCaseStatus(caseResponse.case.status)}</span>
      </div>
      
      <div className="detail-row">
        <span className="field-label">Latest Run</span>
        <span className="status-value">{latestRunStatus ? formatRunStatus(latestRunStatus) : "Pending"}</span>
      </div>

      <div className="detail-row">
        <span className="field-label">Last Updated</span>
        <span className="status-value">{formatDateTime(caseResponse.case.updatedAt)}</span>
      </div>

      {isNeedsReview && (
        <div className="alert warning stack-offset-sm">
          <strong>Needs Human Review</strong>
          <p className="panel-copy-tight">This case requires review before autonomous action is safe.</p>
        </div>
      )}

      {latestRunStatus === "failed" && (
        <div className="alert error stack-offset-sm">
          <strong>Run Failed</strong>
          <p className="panel-copy-tight">
            {failureCategoryMessage ?? "The latest analysis failed before a recommendation was produced."}
          </p>
          {failureReason && <p className="panel-copy-tight">{failureReason}</p>}
        </div>
      )}
    </div>
  );
}
