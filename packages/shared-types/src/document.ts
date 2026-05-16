import type { DocumentType } from "./enums";

export interface DocumentSummary {
  id: string;
  type: DocumentType;
  sourceName: string;
  parseStatus: "pending" | "parsed" | "failed";
}

export interface UploadEmailInput {
  type: "renewal_email";
  sourceName: string;
  emailText: string;
}

