"use client";

import type { DocumentSummary, DocumentType } from "@spendagent/shared-types";
import { useRouter } from "next/navigation";
import { startTransition, useState } from "react";

import { uploadEmailDocument, uploadFileDocument } from "../lib/api-client";

const FILE_TYPES: Array<{ value: Extract<DocumentType, "contract_pdf" | "invoice_pdf" | "usage_csv">; label: string; accept: string }> = [
  { value: "contract_pdf", label: "Contract PDF", accept: ".pdf,application/pdf" },
  { value: "invoice_pdf", label: "Invoice PDF", accept: ".pdf,application/pdf" },
  { value: "usage_csv", label: "Usage CSV", accept: ".csv,text/csv" }
];

export function DocumentUploadPanel({ caseId, documents }: { caseId: string; documents: DocumentSummary[] }) {
  const router = useRouter();
  const [fileType, setFileType] = useState<(typeof FILE_TYPES)[number]["value"]>("contract_pdf");
  const [fileSourceName, setFileSourceName] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [emailSourceName, setEmailSourceName] = useState("renewal-reminder");
  const [emailText, setEmailText] = useState("");
  const [pendingMode, setPendingMode] = useState<"file" | "email" | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedFileConfig = FILE_TYPES.find((item) => item.value === fileType) ?? FILE_TYPES[0];

  const hasContract = documents.some((d) => d.type === "contract_pdf");
  const hasInvoice = documents.some((d) => d.type === "invoice_pdf");
  const hasUsage = documents.some((d) => d.type === "usage_csv");
  const hasEmail = documents.some((d) => d.type === "renewal_email");

  return (
    <section className="card stack">
      <h3 className="panel-title">Evidence Intake</h3>
      
      <ul className="evidence-checklist">
        <li>
          <span>Contract PDF</span> 
          <span className={`pill ${hasContract ? "success" : ""}`}>{hasContract ? "Uploaded" : "Missing"}</span>
        </li>
        <li>
          <span>Invoice PDF</span> 
          <span className={`pill ${hasInvoice ? "success" : ""}`}>{hasInvoice ? "Uploaded" : "Missing"}</span>
        </li>
        <li>
          <span>Usage CSV</span> 
          <span className={`pill ${hasUsage ? "success" : ""}`}>{hasUsage ? "Uploaded" : "Missing"}</span>
        </li>
        <li>
          <span>Renewal Email</span> 
          <span className={`pill ${hasEmail ? "success" : "info"}`}>{hasEmail ? "Uploaded" : "Optional"}</span>
        </li>
      </ul>

      <div className="stack-lg stack-offset-sm">
        <form
          className="stack-sm"
          onSubmit={(event) => {
            event.preventDefault();
            if (!selectedFile) {
              setError("Choose a file before uploading.");
              return;
            }

            setPendingMode("file");
            setError(null);
            setMessage(null);

            startTransition(async () => {
              try {
                await uploadFileDocument(caseId, {
                  type: fileType,
                  sourceName: fileSourceName || selectedFile.name,
                  file: selectedFile
                });
                setMessage(`${selectedFile.name} uploaded successfully.`);
                setFileSourceName("");
                setSelectedFile(null);
                router.refresh();
              } catch (cause) {
                setError(cause instanceof Error ? cause.message : "Failed to upload file");
              } finally {
                setPendingMode(null);
              }
            });
          }}
        >
          <strong className="field-label">Upload file</strong>
          <div className="stack-sm">
            <select value={fileType} onChange={(event) => setFileType(event.target.value as typeof fileType)} disabled={pendingMode !== null}>
              {FILE_TYPES.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <input
              value={fileSourceName}
              onChange={(event) => setFileSourceName(event.target.value)}
              placeholder="Source name (optional)"
              disabled={pendingMode !== null}
            />
            <input
              key={`${fileType}-${selectedFile ? selectedFile.name : "empty"}`}
              type="file"
              accept={selectedFileConfig.accept}
              disabled={pendingMode !== null}
              onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
            />
          </div>
          <button type="submit" className="secondary" disabled={pendingMode !== null}>
            {pendingMode === "file" ? "Uploading..." : "Upload file"}
          </button>
        </form>

        <form
          className="stack-sm"
          onSubmit={(event) => {
            event.preventDefault();
            if (!emailText.trim()) {
              setError("Paste the renewal email text before uploading.");
              return;
            }

            setPendingMode("email");
            setError(null);
            setMessage(null);

            startTransition(async () => {
              try {
                await uploadEmailDocument(caseId, {
                  type: "renewal_email",
                  sourceName: emailSourceName || "renewal-email",
                  emailText
                });
                setMessage("Renewal email uploaded successfully.");
                setEmailText("");
                router.refresh();
              } catch (cause) {
                setError(cause instanceof Error ? cause.message : "Failed to upload renewal email");
              } finally {
                setPendingMode(null);
              }
            });
          }}
        >
          <strong className="field-label">Paste renewal email</strong>
          <div className="stack-sm">
            <input
              value={emailSourceName}
              onChange={(event) => setEmailSourceName(event.target.value)}
              disabled={pendingMode !== null}
              placeholder="Source name"
            />
            <textarea
              value={emailText}
              onChange={(event) => setEmailText(event.target.value)}
              rows={4}
              placeholder="Paste email text here"
              disabled={pendingMode !== null}
            />
          </div>
          <button type="submit" className="secondary" disabled={pendingMode !== null}>
            {pendingMode === "email" ? "Uploading..." : "Upload email"}
          </button>
        </form>
      </div>
      
      {message ? <div className="alert success">{message}</div> : null}
      {error ? <div className="alert error">{error}</div> : null}
    </section>
  );
}
