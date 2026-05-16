import type { DocumentSummary } from "@spendagent/shared-types";
import { formatDocumentType, formatParseStatus } from "../lib/presentation";

export function DocumentList({ documents }: { documents: DocumentSummary[] }) {
  if (documents.length === 0) return null;

  return (
    <div className="card stack">
      <h3 className="panel-title">Uploaded Documents</h3>
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Parse Status</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((document) => {
              let statusClass = "pill";
              if (document.parseStatus === "parsed") statusClass += " success";
              else if (document.parseStatus === "failed") statusClass += " error";
              else statusClass += " info";
              
              return (
                <tr key={document.id}>
                  <td className="status-value">{document.sourceName}</td>
                  <td>{formatDocumentType(document.type)}</td>
                  <td><span className={statusClass}>{formatParseStatus(document.parseStatus)}</span></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
