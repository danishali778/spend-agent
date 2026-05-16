import test from "node:test";
import assert from "node:assert/strict";

import { evaluateEscalation } from "../src/escalation.ts";

test("evaluateEscalation escalates on missing critical facts and low confidence", () => {
  const result = evaluateEscalation({
    missingCriticalFacts: ["renewal_date"],
    confidenceScore: 0.41,
    urgencyLevel: "high",
  });

  assert.equal(result.shouldEscalate, true);
  assert.deepEqual(result.reasons, ["missing_critical_facts", "low_confidence"]);
  assert.deepEqual(result.blockers, ["renewal_date"]);
});

test("evaluateEscalation stays clear when evidence is complete", () => {
  const result = evaluateEscalation({
    missingCriticalFacts: [],
    conflicts: [],
    confidenceScore: 0.82,
    urgencyLevel: "high",
    policyBlocked: false,
  });

  assert.deepEqual(result, {
    shouldEscalate: false,
    blockers: [],
    reasons: [],
  });
});
