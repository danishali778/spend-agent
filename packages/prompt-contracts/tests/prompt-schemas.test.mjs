import assert from "node:assert/strict";
import test from "node:test";

import schemas from "../src/schemas.json" with { type: "json" };

test("prompt bundle version uses documented v1.x.y format", () => {
  assert.match(schemas.bundle.version, /^v\d+\.\d+\.\d+$/);
});

test("all agent schemas publish a version and required keys", () => {
  for (const [agentName, definition] of Object.entries(schemas.schemas)) {
    assert.match(definition.version, /^\d+\.\d+\.\d+$/, `${agentName} version is invalid`);
    assert.ok(Array.isArray(definition.required), `${agentName} required list missing`);
    assert.ok(definition.required.length > 0, `${agentName} required list empty`);
  }
});
