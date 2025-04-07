import { describe, expect, it, vi, beforeEach } from "vitest";
import { formatTimeDelta } from "#/utils/format-time-delta";

describe("formatTimeDelta", () => {
  beforeEach(() => {
    const now = new Date("2024-01-01T00:00:00Z");
    vi.useFakeTimers({ now });
  });

  it("formats the yearly time correctly", () => {
    const oneYearAgo = new Date("2023-01-01T00:00:00Z");
    expect(formatTimeDelta(oneYearAgo)).toBe("1 year");

    const twoYearsAgo = new Date("2022-01-01T00:00:00Z");
    expect(formatTimeDelta(twoYearsAgo)).toBe("2 years");

    const threeYearsAgo = new Date("2021-01-01T00:00:00Z");
    expect(formatTimeDelta(threeYearsAgo)).toBe("3 years");
  });

  it("formats the monthly time correctly", () => {
    const oneMonthAgo = new Date("2023-12-01T00:00:00Z");
    expect(formatTimeDelta(oneMonthAgo)).toBe("1 month");

    const twoMonthsAgo = new Date("2023-11-01T00:00:00Z");
    expect(formatTimeDelta(twoMonthsAgo)).toBe("2 months");

    const threeMonthsAgo = new Date("2023-10-01T00:00:00Z");
    expect(formatTimeDelta(threeMonthsAgo)).toBe("3 months");
  });

  it("formats the daily time correctly", () => {
    const oneDayAgo = new Date("2023-12-31T00:00:00Z");
    expect(formatTimeDelta(oneDayAgo)).toBe("1 day");

    const twoDaysAgo = new Date("2023-12-30T00:00:00Z");
    expect(formatTimeDelta(twoDaysAgo)).toBe("2 days");

    const threeDaysAgo = new Date("2023-12-29T00:00:00Z");
    expect(formatTimeDelta(threeDaysAgo)).toBe("3 days");
  });

  it("formats the hourly time correctly", () => {
    const oneHourAgo = new Date("2023-12-31T23:00:00Z");
    expect(formatTimeDelta(oneHourAgo)).toBe("1 hour");

    const twoHoursAgo = new Date("2023-12-31T22:00:00Z");
    expect(formatTimeDelta(twoHoursAgo)).toBe("2 hours");

    const threeHoursAgo = new Date("2023-12-31T21:00:00Z");
    expect(formatTimeDelta(threeHoursAgo)).toBe("3 hours");
  });

  it("formats the minute time correctly", () => {
    const oneMinuteAgo = new Date("2023-12-31T23:59:00Z");
    expect(formatTimeDelta(oneMinuteAgo)).toBe("1 minute");

    const twoMinutesAgo = new Date("2023-12-31T23:58:00Z");
    expect(formatTimeDelta(twoMinutesAgo)).toBe("2 minutes");

    const threeMinutesAgo = new Date("2023-12-31T23:57:00Z");
    expect(formatTimeDelta(threeMinutesAgo)).toBe("3 minutes");
  });

  it("formats the second time correctly", () => {
    const oneSecondAgo = new Date("2023-12-31T23:59:59Z");
    expect(formatTimeDelta(oneSecondAgo)).toBe("1 second");

    const twoSecondsAgo = new Date("2023-12-31T23:59:58Z");
    expect(formatTimeDelta(twoSecondsAgo)).toBe("2 seconds");

    const threeSecondsAgo = new Date("2023-12-31T23:59:57Z");
    expect(formatTimeDelta(threeSecondsAgo)).toBe("3 seconds");
  });
});
