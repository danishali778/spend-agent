import { CreateCaseForm } from "../../../components/create-case-form";

export default function CreateCasePage() {
  return (
    <div className="stack-lg">
      <div className="section-heading">
        <div className="stack-sm">
          <h1>Create Case</h1>
          <p className="muted">Initialize a new procurement renewal analysis.</p>
        </div>
      </div>
      <div className="case-detail-grid">
        <CreateCaseForm />
        <div className="card stack-sm panel-subtle">
          <h3 className="panel-title">Required Evidence</h3>
          <p className="muted">
            After creating the case, you will need to upload the following documents for analysis:
          </p>
          <ul className="evidence-checklist">
            <li><span>Contract PDF</span> <span className="pill">Required</span></li>
            <li><span>Invoice PDF</span> <span className="pill">Required</span></li>
            <li><span>Usage CSV</span> <span className="pill">Required</span></li>
            <li><span>Renewal Email</span> <span className="pill">Optional</span></li>
          </ul>
        </div>
      </div>
    </div>
  );
}

