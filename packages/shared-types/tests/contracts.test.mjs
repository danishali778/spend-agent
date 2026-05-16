import assert from "node:assert/strict";
import test from "node:test";

import {
  CASE_STATUSES,
  DOCUMENT_TYPES,
  RECOMMENDED_ACTIONS,
  RUN_STATUSES,
  STEP_STATUSES,
} from "../src/enums.ts";

test("shared contract enums keep the documented values", () => {
  assert.ok(CASE_STATUSES.includes("decision_ready"));
  assert.ok(DOCUMENT_TYPES.includes("contract_pdf"));
  assert.ok(RECOMMENDED_ACTIONS.includes("renegotiate"));
  assert.ok(RUN_STATUSES.includes("running"));
  assert.ok(STEP_STATUSES.includes("completed"));
});

