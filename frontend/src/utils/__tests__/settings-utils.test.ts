import { describe, it, expect } from "vitest";
import { parseMaxBudgetPerTask } from "../settings-utils";

describe("parseMaxBudgetPerTask", () => {
  it("should return null for empty string", () => {
    expect(parseMaxBudgetPerTask("")).toBeNull();
  });

  it("should return null for whitespace-only string", () => {
    expect(parseMaxBudgetPerTask("   ")).toBeNull();
  });

  it("should return null for non-numeric string", () => {
    expect(parseMaxBudgetPerTask("abc")).toBeNull();
  });

  it("should return null for values less than 1", () => {
    expect(parseMaxBudgetPerTask("0")).toBeNull();
    expect(parseMaxBudgetPerTask("0.5")).toBeNull();
    expect(parseMaxBudgetPerTask("-1")).toBeNull();
    expect(parseMaxBudgetPerTask("-10.5")).toBeNull();
  });

  it("should return the parsed value for valid numbers >= 1", () => {
    expect(parseMaxBudgetPerTask("1")).toBe(1);
    expect(parseMaxBudgetPerTask("1.0")).toBe(1);
    expect(parseMaxBudgetPerTask("1.5")).toBe(1.5);
    expect(parseMaxBudgetPerTask("10")).toBe(10);
    expect(parseMaxBudgetPerTask("100.99")).toBe(100.99);
  });

  it("should handle string numbers with leading/trailing whitespace", () => {
    expect(parseMaxBudgetPerTask("  1  ")).toBe(1);
    expect(parseMaxBudgetPerTask("  10.5  ")).toBe(10.5);
  });

  it("should return null for edge cases", () => {
    expect(parseMaxBudgetPerTask("0.999")).toBeNull();
    expect(parseMaxBudgetPerTask("NaN")).toBeNull();
    expect(parseMaxBudgetPerTask("Infinity")).toBeNull();
    expect(parseMaxBudgetPerTask("-Infinity")).toBeNull();
  });

  it("should handle scientific notation", () => {
    expect(parseMaxBudgetPerTask("1e0")).toBe(1);
    expect(parseMaxBudgetPerTask("1.5e1")).toBe(15);
    expect(parseMaxBudgetPerTask("5e-1")).toBeNull(); // 0.5, which is < 1
  });
});
