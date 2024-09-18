import { test, expect } from "vitest";
import {
  formatTimestamp,
  getExtension,
  removeApiKey,
} from "../../src/utils/utils";

test("removeApiKey", () => {
  const data = [{ args: { LLM_API_KEY: "key", LANGUAGE: "en" } }];
  expect(removeApiKey(data)).toEqual([{ args: { LANGUAGE: "en" } }]);
});

test("getExtension", () => {
  expect(getExtension("main.go")).toBe("go");
  expect(getExtension("get-extension.test.ts")).toBe("ts");
  expect(getExtension("directory")).toBe("");
});

test("formatTimestamp", () => {
  const morningDate = new Date("2021-10-10T10:10:10.000").toISOString();
  expect(formatTimestamp(morningDate)).toBe("10/10/2021, 10:10:10");

  const eveningDate = new Date("2021-10-10T22:10:10.000").toISOString();
  expect(formatTimestamp(eveningDate)).toBe("10/10/2021, 22:10:10");
});
