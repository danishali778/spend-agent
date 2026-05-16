export type UrgencyLevel = "low" | "medium" | "high" | "critical";

export interface RenewalWindowInput {
  renewalDate: string;
  terminationNoticeDays: number;
  today?: string;
}

export interface RenewalWindowResult {
  status: "ok";
  daysUntilRenewal: number;
  daysUntilNoticeDeadline: number;
  urgencyLevel: UrgencyLevel;
}

const MS_PER_DAY = 24 * 60 * 60 * 1000;

function toUtcDate(input: string): Date {
  const date = new Date(`${input}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) {
    throw new Error(`Invalid date: ${input}`);
  }
  return date;
}

function diffInDays(a: Date, b: Date): number {
  return Math.round((a.getTime() - b.getTime()) / MS_PER_DAY);
}

function deriveUrgencyLevel(daysUntilRenewal: number, daysUntilNoticeDeadline: number): UrgencyLevel {
  if (daysUntilRenewal <= 7 || daysUntilNoticeDeadline <= 0) {
    return "critical";
  }

  if (daysUntilRenewal <= 45 || daysUntilNoticeDeadline <= 30) {
    return "high";
  }

  if (daysUntilRenewal <= 90 || daysUntilNoticeDeadline <= 60) {
    return "medium";
  }

  return "low";
}

export function detectRenewalWindow(input: RenewalWindowInput): RenewalWindowResult {
  if (!Number.isInteger(input.terminationNoticeDays) || input.terminationNoticeDays < 0) {
    throw new Error("terminationNoticeDays must be a non-negative integer");
  }

  const renewalDate = toUtcDate(input.renewalDate);
  const today = toUtcDate(input.today ?? new Date().toISOString().slice(0, 10));
  const daysUntilRenewal = diffInDays(renewalDate, today);
  const noticeDeadline = new Date(renewalDate.getTime() - input.terminationNoticeDays * MS_PER_DAY);
  const daysUntilNoticeDeadline = diffInDays(noticeDeadline, today);

  return {
    status: "ok",
    daysUntilRenewal,
    daysUntilNoticeDeadline,
    urgencyLevel: deriveUrgencyLevel(daysUntilRenewal, daysUntilNoticeDeadline),
  };
}
