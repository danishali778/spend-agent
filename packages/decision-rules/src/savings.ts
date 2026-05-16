export interface SavingsInput {
  currentCost: number;
  currentSeats: number;
  targetSeats: number;
}

export interface SavingsResult {
  status: "ok";
  currentCostPerSeat: number;
  targetCost: number;
  projectedSavings: number;
  seatReduction: number;
}

function assertPositiveNumber(value: number, fieldName: string): void {
  if (!Number.isFinite(value) || value <= 0) {
    throw new Error(`${fieldName} must be greater than zero`);
  }
}

export function estimateSavings(input: SavingsInput): SavingsResult {
  assertPositiveNumber(input.currentCost, "currentCost");

  if (!Number.isInteger(input.currentSeats) || input.currentSeats <= 0) {
    throw new Error("currentSeats must be a positive integer");
  }

  if (!Number.isInteger(input.targetSeats) || input.targetSeats < 0) {
    throw new Error("targetSeats must be a non-negative integer");
  }

  if (input.targetSeats > input.currentSeats) {
    throw new Error("targetSeats cannot exceed currentSeats");
  }

  const currentCostPerSeat = input.currentCost / input.currentSeats;
  const targetCost = currentCostPerSeat * input.targetSeats;
  const projectedSavings = input.currentCost - targetCost;

  return {
    status: "ok",
    currentCostPerSeat: Number(currentCostPerSeat.toFixed(2)),
    targetCost: Number(targetCost.toFixed(2)),
    projectedSavings: Number(projectedSavings.toFixed(2)),
    seatReduction: input.currentSeats - input.targetSeats,
  };
}
