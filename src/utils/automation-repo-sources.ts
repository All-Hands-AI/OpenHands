import type { AutomationRepository } from "#/types/automation";
import type { Provider } from "#/types/settings";

/** A `repos` entry in a preset create or update request. */
export type AutomationRepoSource = {
  url: string;
  ref?: string;
  provider?: string;
};

// The setup picker lists GitHub repositories by their `owner/repo` shorthand,
// and the service needs a provider to clone a shorthand.
const SHORTHAND_PROVIDER = "github";
const FULL_GIT_URL_PATTERN = /^(?:https?:\/\/|git@)/i;

/** Hosts of the providers' hosted services; a connected self-hosted instance supplies its own. */
const PROVIDER_HOSTS: Partial<Record<Provider, string>> = {
  github: "github.com",
  gitlab: "gitlab.com",
  bitbucket: "bitbucket.org",
  azure_devops: "dev.azure.com",
};

/** The host a connected provider is set to, without scheme or path. */
export function providerHost(host: string | null | undefined): string | null {
  const trimmed = host?.trim();
  if (!trimmed) return null;
  try {
    const url = new URL(
      trimmed.includes("://") ? trimmed : `https://${trimmed}`,
    );
    return url.hostname.toLowerCase() || null;
  } catch {
    return null;
  }
}

/**
 * The repository field entry for a repository picked from a provider.
 *
 * GitHub keeps its `owner/repo` shorthand. Other providers, and a GitHub
 * Enterprise host, get the full URL on the connected host or on the provider's
 * hosted service, which the service recognizes and clones with its token.
 */
export function automationRepositoryAddress(
  provider: Provider,
  fullName: string,
  host?: string | null,
): string {
  const configuredHost = providerHost(host);
  if (provider === "github" && !configuredHost) return fullName;
  const hostname = configuredHost ?? PROVIDER_HOSTS[provider];
  if (!hostname) return fullName;
  if (provider === "azure_devops") {
    // Azure DevOps names a repository organization/project/repository.
    const [organization, project, ...rest] = fullName.split("/");
    const repository = rest.join("/");
    if (!organization || !project || !repository) return fullName;
    const path = [organization, project].map(encodeURIComponent).join("/");
    return `https://${hostname}/${path}/_git/${encodeURIComponent(repository)}`;
  }
  return `https://${hostname}/${fullName}`;
}

/**
 * The provider a full URL belongs to when it points at a connected
 * self-hosted instance. A hosted service's URL needs no provider: the service
 * recognizes those hosts itself.
 */
export function providerForAddress(
  url: string,
  hosts: Partial<Record<Provider, string | null>> = {},
): Provider | undefined {
  let hostname: string;
  try {
    hostname = new URL(url).hostname.toLowerCase();
  } catch {
    return undefined;
  }
  for (const [provider, host] of Object.entries(hosts) as [
    Provider,
    string | null,
  ][]) {
    const configured = providerHost(host);
    if (
      configured &&
      configured === hostname &&
      configured !== PROVIDER_HOSTS[provider]
    ) {
      return provider;
    }
  }
  return undefined;
}

/**
 * The `repos` a request sends for the setup form's repositories.
 *
 * A repository the automation already clones keeps its saved branch and
 * provider. A new shorthand is a GitHub repository. A full URL is sent with a
 * provider only when it points at a connected self-hosted host, so the
 * service authenticates its clone for that host and for no other.
 */
export function buildAutomationRepoSources(
  repositories: string[],
  saved: AutomationRepository[] = [],
  hosts: Partial<Record<Provider, string | null>> = {},
): AutomationRepoSource[] {
  return repositories.map((url) => {
    const existing = saved.find((repo) => repo.url === url);
    if (existing) {
      return {
        url: existing.url,
        ...(existing.ref && { ref: existing.ref }),
        ...(existing.provider && { provider: existing.provider }),
      };
    }
    if (!FULL_GIT_URL_PATTERN.test(url)) {
      return { url, provider: SHORTHAND_PROVIDER };
    }
    const provider = providerForAddress(url, hosts);
    return provider ? { url, provider } : { url };
  });
}

/** Whether the form lists other repositories than the automation clones. */
export function automationRepositoriesChanged(
  repositories: string[],
  saved: AutomationRepository[] = [],
): boolean {
  return (
    repositories.length !== saved.length ||
    repositories.some((url, index) => url !== saved[index]?.url)
  );
}

/** Repositories in the setup form's comma-separated shape. */
export function formatAutomationRepositories(
  repositories: AutomationRepository[] = [],
): string {
  return repositories
    .map((repo) => repo.url.trim())
    .filter(Boolean)
    .join(", ");
}
