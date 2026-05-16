"use client";

import type { GeneratedArtifact, RunFailureCategory, RunStatus } from "@spendagent/shared-types";
import { useState } from "react";
import { formatArtifactType, formatDateTime, formatFailureCategory } from "../lib/presentation";

const ARTIFACT_ORDER = ["cfo_summary", "approval_note", "vendor_email"];

export function ArtifactViewer({
  artifacts,
  latestRunStatus,
  latestRunFailureCategory,
}: {
  artifacts: GeneratedArtifact[];
  latestRunStatus?: RunStatus | null;
  latestRunFailureCategory?: RunFailureCategory | null;
}) {
  const [activeTabIndex, setActiveTabIndex] = useState(0);
  const [copied, setCopied] = useState(false);

  if (artifacts.length === 0) {
    return (
      <div className="card stack">
        <h3 className="panel-title">Generated Artifacts</h3>
        <div className="alert info">
          <strong>{latestRunStatus === "failed" ? "Artifact Generation Failed" : "Pending Generation"}</strong>
          <p className="panel-copy">
            {latestRunStatus === "failed"
              ? formatFailureCategory(latestRunFailureCategory) ?? "The latest analysis failed before draft artifacts could be generated."
              : "Once analysis completes, SpendAgent will show the CFO summary, approval note, and vendor email here."}
          </p>
        </div>
      </div>
    );
  }

  // Pre-sort artifacts
  const sortedArtifacts = [...artifacts].sort((a, b) => {
    const aIdx = ARTIFACT_ORDER.indexOf(a.artifactType);
    const bIdx = ARTIFACT_ORDER.indexOf(b.artifactType);
    return (aIdx === -1 ? 99 : aIdx) - (bIdx === -1 ? 99 : bIdx);
  });

  const activeArtifact = sortedArtifacts[activeTabIndex] || sortedArtifacts[0];

  const handleCopy = async () => {
    if (!activeArtifact) return;
    try {
      await navigator.clipboard.writeText(activeArtifact.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  return (
    <div className="card stack">
      <div className="section-heading">
        <h3 className="panel-title">Generated Artifacts</h3>
        <button onClick={handleCopy} className="secondary compact-action">
          {copied ? "Copied!" : "Copy Draft"}
        </button>
      </div>
      
      <div className="artifact-tabs">
        {sortedArtifacts.map((artifact, index) => (
          <button
            key={`${artifact.artifactType}-${index}`}
            className={`artifact-tab ${index === activeTabIndex ? "active" : ""}`}
            onClick={() => setActiveTabIndex(index)}
          >
            {formatArtifactType(artifact.artifactType)}
          </button>
        ))}
      </div>

      {activeArtifact && (
        <div className="artifact-content stack-sm">
          <div className="detail-row">
            <strong className="panel-title">{activeArtifact.title}</strong>
            {activeArtifact.createdAt ? (
              <span className="muted artifact-meta">
                {formatDateTime(activeArtifact.createdAt)}
              </span>
            ) : null}
          </div>
          <div className="artifact-draft">
            {activeArtifact.content}
          </div>
        </div>
      )}
    </div>
  );
}
