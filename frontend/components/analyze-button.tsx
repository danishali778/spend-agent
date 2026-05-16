"use client";

import { useRouter } from "next/navigation";
import { startTransition, useState } from "react";

import { analyzeCase, getActivity } from "../lib/api-client";

export function AnalyzeButton({ caseId }: { caseId: string }) {
  const router = useRouter();
  const [status, setStatus] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  return (
    <div className="row">
      <button
        disabled={pending}
        onClick={() => {
          startTransition(async () => {
            setPending(true);
            const response = await analyzeCase(caseId);
            setStatus(`Run ${response.runId} is ${response.status}`);

            const startedAt = Date.now();
            const timeoutMs = 45_000;

            while (Date.now() - startedAt < timeoutMs) {
              await new Promise((resolve) => setTimeout(resolve, 1500));
              const activity = await getActivity(caseId);
              if (!activity) {
                continue;
              }
              setStatus(`Run ${activity.runId} is ${activity.status}`);
              if (activity.status === "completed" || activity.status === "failed" || activity.status === "cancelled") {
                router.refresh();
                setPending(false);
                return;
              }
            }

            setPending(false);
            router.refresh();
          });
        }}
      >
        {pending ? "Analyzing..." : "Trigger Analysis"}
      </button>
      {status ? <span>{status}</span> : null}
    </div>
  );
}
