export interface UtilizationInput {
  seatsPurchased: number;
  seatsActive: number;
}

export interface UtilizationResult {
  status: "ok";
  utilizationPercent: number;
  inactiveSeats: number;
  activeSeatRatio: number;
}

function assertNonNegativeInteger(value: number, fieldName: string): void {
  if (!Number.isInteger(value) || value < 0) {
    throw new Error(`${fieldName} must be a non-negative integer`);
  }
}

export function computeUtilization(input: UtilizationInput): UtilizationResult {
  assertNonNegativeInteger(input.seatsPurchased, "seatsPurchased");
  assertNonNegativeInteger(input.seatsActive, "seatsActive");

  if (input.seatsPurchased === 0) {
    throw new Error("seatsPurchased must be greater than zero");
  }

  if (input.seatsActive > input.seatsPurchased) {
    throw new Error("seatsActive cannot exceed seatsPurchased");
  }

  const activeSeatRatio = input.seatsActive / input.seatsPurchased;
  return {
    status: "ok",
    utilizationPercent: Number((activeSeatRatio * 100).toFixed(2)),
    inactiveSeats: input.seatsPurchased - input.seatsActive,
    activeSeatRatio: Number(activeSeatRatio.toFixed(4)),
  };
}
