import { removeApiKey } from "./utils";

test("removeApiKey", () => {
  const data = [{ args: { LLM_API_KEY: "key", LANGUAGE: "en" } }];
  expect(removeApiKey(data)).toEqual([{ args: { LANGUAGE: "en" } }]);
});
