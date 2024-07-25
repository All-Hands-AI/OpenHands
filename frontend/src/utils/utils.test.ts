import { getExtension, removeApiKey } from "./utils";

test("removeApiKey", () => {
  const data = [{ args: { LLM_API_KEY: "key", LANGUAGE: "en" } }];
  expect(removeApiKey(data)).toEqual([{ args: { LANGUAGE: "en" } }]);
});

test("getExtension", () => {
  expect(getExtension("main.go")).toBe("go");
  expect(getExtension("get-extension.test.ts")).toBe("ts");
  expect(getExtension("directory")).toBe("");
});
