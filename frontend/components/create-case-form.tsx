"use client";

import { useRouter } from "next/navigation";
import { startTransition, useState } from "react";

import { createCase } from "../lib/api-client";

export function CreateCaseForm() {
  const router = useRouter();
  const [vendorName, setVendorName] = useState("");
  const [renewalDate, setRenewalDate] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <form
      className="stack card"
      onSubmit={(event) => {
        event.preventDefault();
        setPending(true);
        setError(null);
        startTransition(async () => {
          try {
            const response = await createCase({
              vendorName,
              renewalDate: renewalDate ? (renewalDate.includes("T") ? renewalDate : `${renewalDate}T00:00:00Z`) : undefined,
              ownerUserId: "00000000-0000-0000-0000-000000000001"
            });
            router.push(`/cases/${response.case.id}`);
          } catch (cause) {
            setError(cause instanceof Error ? cause.message : "Failed to create case");
          } finally {
            setPending(false);
          }
        });
      }}
    >
      <div className="stack-sm">
        <label className="stack-sm">
          <span className="field-label">Vendor Name</span>
          <input value={vendorName} onChange={(event) => setVendorName(event.target.value)} required />
        </label>
        <label className="stack-sm">
          <span className="field-label">Renewal Date (Optional)</span>
          <input type="date" value={renewalDate} onChange={(event) => setRenewalDate(event.target.value)} />
        </label>
      </div>
      
      {error ? <div className="alert error">{error}</div> : null}
      
      <div className="stack-offset-sm">
        <button type="submit" disabled={pending}>{pending ? "Creating..." : "Create Case"}</button>
      </div>
    </form>
  );
}
