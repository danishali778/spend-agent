import Link from "next/link";
import type { CaseSummary } from "@spendagent/shared-types";
import { formatCaseStatus, formatRecommendedAction, formatShortDate } from "../lib/presentation";
import { formatProjectedSavings } from "../lib/projected-savings";

export function CaseTable({ items }: { items: CaseSummary[] }) {
  if (items.length === 0) {
    return (
      <div className="card stack empty-state-card">
        <p className="muted empty-state-copy">No renewal cases yet. Create a case to start evidence intake and analysis.</p>
        <div>
          <Link href="/cases/new">
            <button>Create Case</button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="table-container">
      <table>
        <thead>
          <tr>
            <th>Vendor</th>
            <th>Status</th>
            <th>Renewal Date</th>
            <th>Projected Savings</th>
            <th>Recommended Action</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => {
            let statusPillClass = "pill";
            if (item.status === "decision_ready") statusPillClass += " success";
            else if (item.status === "needs_review") statusPillClass += " error";
            else statusPillClass += " info";
            
            return (
              <tr key={item.id}>
                <td className="status-value">
                  <Link href={`/cases/${item.id}`}>{item.vendorName}</Link>
                </td>
                <td><span className={statusPillClass}>{formatCaseStatus(item.status)}</span></td>
                <td>{formatShortDate(item.renewalDate)}</td>
                <td>{formatProjectedSavings(item)}</td>
                <td>{formatRecommendedAction(item.recommendedAction)}</td>
                <td className="status-value">
                  <Link href={`/cases/${item.id}`}>
                    <button className="secondary compact-action">View Case</button>
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
