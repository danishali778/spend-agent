export interface GeneratedArtifact {
  artifactType: "cfo_summary" | "approval_note" | "vendor_email";
  title: string;
  content: string;
  decisionVersion: number;
  createdAt: string;
}

