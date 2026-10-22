import { describe, expect, it } from "vitest";
import {
  automationRepositoryAddress,
  buildAutomationRepoSources,
  providerBaseUrl,
  providerForAddress,
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

  it("keeps a self-hosted instance's port and path prefix", () => {
    expect(
      automationRepositoryAddress(
        "gitlab",
        "acme/tools",
        "https://git.example.com:8443",
      ),
    ).toBe("https://git.example.com:8443/acme/tools");
    expect(
      automationRepositoryAddress(
        "bitbucket_data_center",
        "PROJ/repo",
        "https://example.com/bitbucket/",
      ),
    ).toBe("https://example.com/bitbucket/PROJ/repo");
    expect(
      automationRepositoryAddress(
        "azure_devops",
        "fabrikam/Fabrikam Fiber/fabrikam-web",
        "https://devops.example.com:8080/tfs",
      ),
    ).toBe(
      "https://devops.example.com:8080/tfs/fabrikam/Fabrikam%20Fiber/_git/fabrikam-web",
    );
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

describe("providerBaseUrl", () => {
  it("normalizes a configured host to its base URL", () => {
    expect(providerBaseUrl("https://gitlab.example.com/")).toBe(
      "https://gitlab.example.com",
    );
    expect(providerBaseUrl("Gitlab.Example.com")).toBe(
      "https://gitlab.example.com",
    );
    expect(providerBaseUrl("https://git.example.com:8443")).toBe(
      "https://git.example.com:8443",
    );
    expect(providerBaseUrl("http://example.com/gitlab/")).toBe(
      "http://example.com/gitlab",
    );
    expect(providerBaseUrl("")).toBeNull();
    expect(providerBaseUrl(null)).toBeNull();
    expect(providerBaseUrl("not a host")).toBeNull();
  });
});

describe("providerForAddress", () => {
  const hosts = {
    gitlab: "https://git.example.com:8443",
    bitbucket_data_center: "https://example.com/bitbucket/",
    github: null,
    azure_devops: "https://devops.example.com",
  };

  it("names the provider of a connected self-hosted instance", () => {
    expect(
      providerForAddress("https://git.example.com:8443/acme/tools", hosts),
    ).toBe("gitlab");
    expect(
      providerForAddress("https://example.com/bitbucket/PROJ/repo", hosts),
    ).toBe("bitbucket_data_center");
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
    // Same hostname on another port, or outside the prefix, is not the instance.
    expect(
      providerForAddress("https://git.example.com/acme/tools", hosts),
    ).toBe(undefined);
    expect(providerForAddress("https://example.com/other/x", hosts)).toBe(
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
    expect(
      buildAutomationRepoSources(
        ["https://git.example.com:8443/acme/tools"],
        [],
        { gitlab: "https://git.example.com:8443" },
      ),
    ).toEqual([
      { url: "https://git.example.com:8443/acme/tools", provider: "gitlab" },
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
