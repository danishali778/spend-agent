import type { AgentActivityEvent, RunFailureCategory, RunStatus } from "@spendagent/shared-types";
import { formatAgentName, formatEventTime, formatFailureCategory, formatStepName, formatStepStatus } from "../lib/presentation";

export function AgentTimeline({
  events,
  latestRunStatus,
  latestRunFailureCategory,
  latestRunFailureReason,
}: {
  events: AgentActivityEvent[];
  latestRunStatus?: RunStatus | null;
  latestRunFailureCategory?: RunFailureCategory | null;
  latestRunFailureReason?: string | null;
}) {
  if (events.length === 0) {
    return (
      <div className="card stack">
        <h3 className="panel-title">Activity Timeline</h3>
        <p className="muted">
          {latestRunStatus === "failed" 
            ? "The latest run did not produce a complete activity timeline." 
            : "No run activity yet. Trigger analysis to start."}
        </p>
      </div>
    );
  }

  return (
    <div className="card stack-sm">
      <h3 className="panel-title">Activity Timeline</h3>
      
      <div className="timeline-list">
        {events.map((event) => (
          <div key={`${event.runId}-${event.agentName}-${event.stepName}`} className="timeline-item">
            <div className="timeline-meta">
              <div>
                <span className="pill info timeline-agent-pill">{formatAgentName(event.agentName)}</span>
                <strong>{formatStepName(event.stepName)}</strong>
              </div>
              <span className="muted artifact-meta">{formatEventTime(event) ?? "Waiting"}</span>
            </div>
            
            <div className="detail-row">
              <span className={`timeline-status ${event.status}`}>
                {formatStepStatus(event.status)}
              </span>
              {event.summary && <span className="muted">— {event.summary}</span>}
            </div>
            
            {event.error ? (
              <div className="alert error timeline-error">
                {JSON.stringify(event.error)}
              </div>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}
