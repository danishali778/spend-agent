import Link from "next/link";
import { CaseTable } from "../components/case-table";
import { MetricCards } from "../components/metric-cards";
import { listCases } from "../lib/api-client";

export default async function HomePage() {
  const response = await listCases();
  return (
    <div className="stack-lg">
      <div className="section-heading">
        <div className="stack-sm">
          <h1>Work Queue</h1>
          <p className="muted">Manage and review vendor renewals.</p>
        </div>
        <Link href="/cases/new">
          <button>Create Case</button>
        </Link>
      </div>
      <MetricCards items={response.items} />
      <CaseTable items={response.items} />
    </div>
  );
}
