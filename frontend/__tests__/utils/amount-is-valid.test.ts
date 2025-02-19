import { describe, expect, test } from "vitest";
import { amountIsValid } from "#/utils/amount-is-valid";

describe("amountIsValid", () => {
  describe("fails", () => {
    test("when the amount is negative", () => {
      expect(amountIsValid("-5")).toBe(false);
      expect(amountIsValid("-25")).toBe(false);
    });

    test("when the amount is zero", () => {
      expect(amountIsValid("0")).toBe(false);
    });

    test("when an empty string is passed", () => {
      expect(amountIsValid("")).toBe(false);
      expect(amountIsValid("     ")).toBe(false);
    });

    test("when a non-numeric value is passed", () => {
      expect(amountIsValid("abc")).toBe(false);
      expect(amountIsValid("1abc")).toBe(false);
      expect(amountIsValid("abc1")).toBe(false);
    });

    test("when an amount less than the minimum is passed", () => {
      // test assumes the minimum is 25
      expect(amountIsValid("24")).toBe(false);
      expect(amountIsValid("24.99")).toBe(false);
    });
  });
});
