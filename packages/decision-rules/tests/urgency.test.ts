import test from "node:test";
import assert from "node:assert/strict";

import { detectRenewalWindow } from "../src/urgency.ts";

test("detectRenewalWindow matches the sample-case timing", () => {
  const result = detectRenewalWindow({
    renewalDate: "2026-06-18",
    terminationNoticeDays: 14,
    today: "2026-05-08",
  });

  assert.deepEqual(result, {
    status: "ok",
    daysUntilRenewal: 41,
    daysUntilNoticeDeadline: 27,
    urgencyLevel: "high",
  });
});

test("detectRenewalWindow becomes critical at or past notice deadline", () => {
  const result = detectRenewalWindow({
    renewalDate: "2026-06-18",
    terminationNoticeDays: 14,
    today: "2026-06-05",
  });

  assert.equal(result.urgencyLevel, "critical");
  assert.equal(result.daysUntilNoticeDeadline, -1);
});
