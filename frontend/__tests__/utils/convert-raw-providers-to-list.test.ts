import { describe, expect, it } from "vitest";
import { Provider, ProviderTokenSettings } from "#/types/settings";
import { convertRawProvidersToList } from "#/utils/convert-raw-providers-to-list";

describe("convertRawProvidersToList", () => {
  it("should convert raw provider tokens to a list of providers", () => {
    const example1:
      | Partial<Record<Provider, ProviderTokenSettings | null>>
      | undefined = {
      github: { host: "github.com" },
      gitlab: { host: "gitlab.com" },
    };
    const example2:
      | Partial<Record<Provider, ProviderTokenSettings | null>>
      | undefined = {
      github: { host: "" },
    };
    const example3:
      | Partial<Record<Provider, ProviderTokenSettings | null>>
      | undefined = {
      gitlab: null,
    };

    expect(convertRawProvidersToList(example1)).toEqual(["github", "gitlab"]);
    expect(convertRawProvidersToList(example2)).toEqual(["github"]);
    expect(convertRawProvidersToList(example3)).toEqual([]);
  });
});
