import { describe, expect, it } from "vitest";
import { Provider } from "#/types/settings";
import { convertRawProvidersToList } from "#/utils/convert-raw-providers-to-list";

describe("convertRawProvidersToList", () => {
  it("should convert raw provider tokens to a list of providers", () => {
    const example: Partial<Record<Provider, string | null>> | undefined = {
      github: "test-token",
      gitlab: "test-token",
    };

    expect(convertRawProvidersToList(example)).toEqual(["github", "gitlab"]);
  });

  it("should handle empty values", () => {
    const example1: Partial<Record<Provider, string | null>> | undefined = {
      github: "test-token",
      gitlab: "",
    };

    const example2: Partial<Record<Provider, string | null>> | undefined = {
      github: null,
      gitlab: "test-token",
    };

    expect(convertRawProvidersToList(example1)).toEqual(["github"]);
    expect(convertRawProvidersToList(example2)).toEqual(["gitlab"]);
  });

  it("should return an empty list for undefined input", () => {
    expect(convertRawProvidersToList(undefined)).toEqual([]);
  });
});
