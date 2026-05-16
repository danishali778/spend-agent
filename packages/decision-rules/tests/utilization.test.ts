import test from "node:test";
import assert from "node:assert/strict";

import { computeUtilization } from "../src/utilization.ts";

test("computeUtilization returns percent and inactive seats", () => {
  const result = computeUtilization({ seatsPurchased: 250, seatsActive: 46 });

  assert.deepEqual(result, {
    status: "ok",
    utilizationPercent: 18.4,
    inactiveSeats: 204,
    activeSeatRatio: 0.184,
  });
});

test("computeUtilization rejects invalid seat counts", () => {
  assert.throws(
    () => computeUtilization({ seatsPurchased: 25, seatsActive: 26 }),
    /cannot exceed/,
  );
});
