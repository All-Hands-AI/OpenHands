import { test, expect } from "vitest";
import { isNumber } from "../../src/utils/is-number";

test("isNumber", () => {
  expect(isNumber(1)).toBe(true);
  expect(isNumber(0)).toBe(true);
  expect(isNumber("3")).toBe(true);
  expect(isNumber("0")).toBe(true);
});
