import { describe, expect, it } from "vitest";
import {
  automationRepositoryAddress,
  buildAutomationRepoSources,
  providerForAddress,
  providerHost,
} from "#/utils/automation-repo-sources";

describe("automationRepositoryAddress", () => {
  it("keeps GitHub's owner/repo shorthand", () => {
    expect(automationRepositoryAddress("github", "OpenHands/OpenHands")).toBe(
      "OpenHands/OpenHands",
    );
    expect(
      automationRepositoryAddress("github", "OpenHands/OpenHands", null),
    ).toBe("OpenHands/OpenHands");
  });

  it("uses the provider's hosted service for GitLab and Bitbucket", () => {
    expect(automationRepositoryAddress("gitlab", "acme/tools")).toBe(
      "https://gitlab.com/acme/tools",
    );
    expect(automationRepositoryAddress("bitbucket", "acme/tools")).toBe(
      "https://bitbucket.org/acme/tools",
    );
  });

  it("uses a connected self-hosted host, with or without a scheme", () => {
    expect(
      automationRepositoryAddress(
        "gitlab",
        "acme/tools",
        "https://gitlab.example.com/",
      ),
    ).toBe("https://gitlab.example.com/acme/tools");
    expect(
      automationRepositoryAddress("github", "acme/tools", "GitHub.Example.com"),
    ).toBe("https://github.example.com/acme/tools");
  });

  it("builds an Azure DevOps _git URL from organization/project/repository", () => {
    expect(
      automationRepositoryAddress(
        "azure_devops",
        "fabrikam/Fabrikam Fiber/fabrikam-web",
      ),
    ).toBe("https://dev.azure.com/fabrikam/Fabrikam%20Fiber/_git/fabrikam-web");
    // A name that is not organization/project/repository is kept as it is.
    expect(automationRepositoryAddress("azure_devops", "fabrikam/web")).toBe(
      "fabrikam/web",
    );
  });

  it("keeps the name for a provider without a hosted service", () => {
    expect(
      automationRepositoryAddress("bitbucket_data_center", "PROJ/repo"),
    ).toBe("PROJ/repo");
  });
});

describe("providerHost", () => {
  it("reduces a configured host to its hostname", () => {
    expect(providerHost("https://gitlab.example.com/path")).toBe(
      "gitlab.example.com",
    );
    expect(providerHost("Gitlab.Example.com")).toBe("gitlab.example.com");
    expect(providerHost("")).toBeNull();
    expect(providerHost(null)).toBeNull();
    expect(providerHost("not a host")).toBeNull();
  });
});

describe("providerForAddress", () => {
  const hosts = {
    gitlab: "https://gitlab.example.com",
    github: null,
    azure_devops: "https://devops.example.com",
  };

  it("names the provider of a connected self-hosted host", () => {
    expect(
      providerForAddress("https://gitlab.example.com/acme/tools", hosts),
    ).toBe("gitlab");
    expect(
      providerForAddress("https://devops.example.com/o/p/_git/r", hosts),
    ).toBe("azure_devops");
  });

  it("leaves hosted services and unknown hosts without a provider", () => {
    expect(providerForAddress("https://gitlab.com/acme/tools", hosts)).toBe(
      undefined,
    );
    expect(providerForAddress("https://github.com/acme/tools", hosts)).toBe(
      undefined,
    );
    expect(providerForAddress("https://other.example.com/x/y", hosts)).toBe(
      undefined,
    );
    expect(providerForAddress("not a url", hosts)).toBe(undefined);
  });
});

describe("buildAutomationRepoSources", () => {
  it("sends shorthands as GitHub and hosted URLs without a provider", () => {
    expect(
      buildAutomationRepoSources([
        "OpenHands/OpenHands",
        "https://gitlab.com/acme/tools",
      ]),
    ).toEqual([
      { url: "OpenHands/OpenHands", provider: "github" },
      { url: "https://gitlab.com/acme/tools" },
    ]);
  });

  it("sends the provider for a URL on a connected self-hosted host", () => {
    expect(
      buildAutomationRepoSources(
        ["https://gitlab.example.com/acme/tools"],
        [],
        {
          gitlab: "https://gitlab.example.com",
        },
      ),
    ).toEqual([
      { url: "https://gitlab.example.com/acme/tools", provider: "gitlab" },
    ]);
  });

  it("keeps a saved repository's branch and provider", () => {
    expect(
      buildAutomationRepoSources(
        ["https://gitlab.example.com/acme/tools"],
        [
          {
            url: "https://gitlab.example.com/acme/tools",
            ref: "main",
            provider: "gitlab",
          },
        ],
        {},
      ),
    ).toEqual([
      {
        url: "https://gitlab.example.com/acme/tools",
        ref: "main",
        provider: "gitlab",
      },
    ]);
  });
});
