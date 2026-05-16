import test from "node:test";
import assert from "node:assert/strict";

import { estimateSavings } from "../src/savings.ts";

test("estimateSavings uses a linear seat-cost model", () => {
  const result = estimateSavings({
    currentCost: 48000,
    currentSeats: 250,
    targetSeats: 120,
  });

  assert.deepEqual(result, {
    status: "ok",
    currentCostPerSeat: 192,
    targetCost: 23040,
    projectedSavings: 24960,
    seatReduction: 130,
  });
});

test("estimateSavings rejects target seats above current baseline", () => {
  assert.throws(
    () => estimateSavings({ currentCost: 48000, currentSeats: 250, targetSeats: 300 }),
    /cannot exceed/,
  );
});
