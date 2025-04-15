import { test, expect } from "vitest";
import { formatMs } from "../../src/utils/format-ms";

test("formatMs", () => {
  expect(formatMs(1000)).toBe("00:01");
  expect(formatMs(1000 * 60)).toBe("01:00");
  expect(formatMs(1000 * 60 * 2.5)).toBe("02:30");
  expect(formatMs(1000 * 60 * 12)).toBe("12:00");
});
