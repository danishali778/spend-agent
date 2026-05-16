import assert from "node:assert/strict";
import test from "node:test";

import commsSchema from "../src/comms-agent.schema.json" with { type: "json" };
import decisionSchema from "../src/decision-agent.schema.json" with { type: "json" };
import documentSchema from "../src/document-agent.schema.json" with { type: "json" };
import financeSchema from "../src/finance-agent.schema.json" with { type: "json" };
import policySchema from "../src/policy-agent.schema.json" with { type: "json" };
import { PROMPT_BUNDLE_VERSION } from "../src/prompt-versions.ts";

test("prompt schemas expose a bundle version and required keys", () => {
  assert.equal(PROMPT_BUNDLE_VERSION, "v1.0.0");
  assert.ok(documentSchema.required.includes("facts"));
  assert.ok(financeSchema.required.includes("usageSnapshot"));
  assert.ok(policySchema.required.includes("checks"));
  assert.ok(decisionSchema.required.includes("recommendedAction"));
  assert.ok(commsSchema.required.includes("artifacts"));
});

