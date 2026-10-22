import type { AutomationRepository } from "#/types/automation";

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

/**
 * The `repos` a request sends for the setup form's repositories.
 *
 * A repository the automation already clones keeps its saved branch and
 * provider. A new shorthand is a GitHub repository. A full URL is sent without
 * a provider, so the service authenticates its clone only for that URL's own
 * host.
 */
export function buildAutomationRepoSources(
  repositories: string[],
  saved: AutomationRepository[] = [],
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
    return FULL_GIT_URL_PATTERN.test(url)
      ? { url }
      : { url, provider: SHORTHAND_PROVIDER };
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
