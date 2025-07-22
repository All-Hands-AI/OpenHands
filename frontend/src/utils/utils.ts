import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { Provider } from "#/types/settings";
import { ConversationStatus } from "#/types/conversation-status";
import { RuntimeStatus } from "#/types/runtime-status";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface EventActionHistory {
  args?: {
    LLM_API_KEY?: string;
    [key: string]: unknown;
  };
  extras?: {
    open_page_urls: string[];
    active_page_index: number;
    dom_object: Record<string, unknown>;
    axtree_object: Record<string, unknown>;
    extra_element_properties: Record<string, unknown>;
    last_browser_action: string;
    last_browser_action_error: unknown;
    focused_element_bid: string;
  };
  [key: string]: unknown;
}

export const removeUnwantedKeys = (
  data: EventActionHistory[],
): EventActionHistory[] => {
  const UNDESIRED_KEYS = [
    "open_page_urls",
    "active_page_index",
    "dom_object",
    "axtree_object",
    "extra_element_properties",
    "last_browser_action",
    "last_browser_action_error",
    "focused_element_bid",
  ];

  return data
    .filter((item) => {
      // Skip items that have a status key
      if ("status" in item) {
        return false;
      }
      return true;
    })
    .map((item) => {
      // Create a shallow copy of item
      const newItem = { ...item };

      // Check if extras exists and delete it from a new extras object
      if (newItem.extras) {
        const newExtras = { ...newItem.extras };
        UNDESIRED_KEYS.forEach((key) => {
          delete newExtras[key as keyof typeof newExtras];
        });
        newItem.extras = newExtras;
      }

      return newItem;
    });
};

export const removeApiKey = (
  data: EventActionHistory[],
): EventActionHistory[] =>
  data.map((item) => {
    // Create a shallow copy of item
    const newItem = { ...item };

    // Check if LLM_API_KEY exists and delete it from a new args object
    if (newItem.args?.LLM_API_KEY) {
      const newArgs = { ...newItem.args };
      delete newArgs.LLM_API_KEY;
      newItem.args = newArgs;
    }

    return newItem;
  });

export const getExtension = (code: string) => {
  if (code.includes(".")) return code.split(".").pop() || "";
  return "";
};

/**
 * Format a timestamp to a human-readable format
 * @param timestamp The timestamp to format (ISO 8601)
 * @returns The formatted timestamp
 *
 * @example
 * formatTimestamp("2021-10-10T10:10:10.000") // "10/10/2021, 10:10:10"
 * formatTimestamp("2021-10-10T22:10:10.000") // "10/10/2021, 22:10:10"
 */
export const formatTimestamp = (timestamp: string) =>
  new Date(timestamp).toLocaleString("en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

export const getGitProviderBaseUrl = (gitProvider: Provider): string => {
  switch (gitProvider) {
    case "github":
      return "https://github.com";
    case "gitlab":
      return "https://gitlab.com";
    case "bitbucket":
      return "https://bitbucket.org";
    default:
      return "";
  }
};

/**
 * Get the default branch name for a git provider
 * @param gitProvider The git provider
 * @returns The default branch name for the provider
 *
 * @example
 * getDefaultBranch("github") // "main"
 * getDefaultBranch("gitlab") // "main"
 * getDefaultBranch("bitbucket") // "main"
 */
export const getDefaultBranch = (gitProvider: Provider): string => {
  switch (gitProvider) {
    case "github":
      return "main";
    case "gitlab":
      return "main";
    case "bitbucket":
      return "main";
    default:
      return "main";
  }
};

/**
 * Get the name of the git provider
 * @param gitProvider The git provider
 * @returns The name of the git provider
 */
export const getProviderName = (gitProvider: Provider) => {
  if (gitProvider === "gitlab") return "GitLab";
  if (gitProvider === "bitbucket") return "Bitbucket";
  return "GitHub";
};

/**
 * Get the name of the PR
 * @param isGitLab Whether the git provider is GitLab
 * @returns The name of the PR
 */
export const getPR = (isGitLab: boolean) =>
  isGitLab ? "merge request" : "pull request";

/**
 * Get the short name of the PR
 * @param isGitLab Whether the git provider is GitLab
 * @returns The short name of the PR
 */
export const getPRShort = (isGitLab: boolean) => (isGitLab ? "MR" : "PR");

/**
 * Construct the pull request (merge request) URL for different providers
 * @param prNumber The pull request number
 * @param provider The git provider
 * @param repositoryName The repository name in format "owner/repo"
 * @returns The pull request URL
 *
 * @example
 * constructPullRequestUrl(123, "github", "owner/repo") // "https://github.com/owner/repo/pull/123"
 * constructPullRequestUrl(456, "gitlab", "owner/repo") // "https://gitlab.com/owner/repo/-/merge_requests/456"
 * constructPullRequestUrl(789, "bitbucket", "owner/repo") // "https://bitbucket.org/owner/repo/pull-requests/789"
 */
export const constructPullRequestUrl = (
  prNumber: number,
  provider: Provider,
  repositoryName: string,
): string => {
  const baseUrl = getGitProviderBaseUrl(provider);

  switch (provider) {
    case "github":
      return `${baseUrl}/${repositoryName}/pull/${prNumber}`;
    case "gitlab":
      return `${baseUrl}/${repositoryName}/-/merge_requests/${prNumber}`;
    case "bitbucket":
      return `${baseUrl}/${repositoryName}/pull-requests/${prNumber}`;
    default:
      return "";
  }
};

/**
 * Construct the microagent URL for different providers
 * @param gitProvider The git provider
 * @param repositoryName The repository name in format "owner/repo"
 * @param microagentPath The path to the microagent in the repository
 * @returns The URL to the microagent file in the Git provider
 *
 * @example
 * constructMicroagentUrl("github", "owner/repo", ".openhands/microagents/tell-me-a-joke.md")
 * // "https://github.com/owner/repo/blob/main/.openhands/microagents/tell-me-a-joke.md"
 * constructMicroagentUrl("gitlab", "owner/repo", "microagents/git-helper.md")
 * // "https://gitlab.com/owner/repo/-/blob/main/microagents/git-helper.md"
 * constructMicroagentUrl("bitbucket", "owner/repo", ".openhands/microagents/docker-helper.md")
 * // "https://bitbucket.org/owner/repo/src/main/.openhands/microagents/docker-helper.md"
 */
export const constructMicroagentUrl = (
  gitProvider: Provider,
  repositoryName: string,
  microagentPath: string,
): string => {
  const baseUrl = getGitProviderBaseUrl(gitProvider);

  switch (gitProvider) {
    case "github":
      return `${baseUrl}/${repositoryName}/blob/main/${microagentPath}`;
    case "gitlab":
      return `${baseUrl}/${repositoryName}/-/blob/main/${microagentPath}`;
    case "bitbucket":
      return `${baseUrl}/${repositoryName}/src/main/${microagentPath}`;
    default:
      return "";
  }
};

export const isConversationStarting = (
  conversationStatus: ConversationStatus | null | undefined,
  runtimeStatus: RuntimeStatus | null | undefined,
) =>
  conversationStatus === "STARTING" ||
  runtimeStatus === "STATUS$STARTING_RUNTIME";

export const isConversationStopped = (
  conversationStatus: ConversationStatus | null | undefined,
  runtimeStatus: RuntimeStatus | null | undefined,
) => conversationStatus === "STOPPED" || runtimeStatus === "STATUS$STOPPED";

export const isConversationError = (
  runtimeStatus: RuntimeStatus | null | undefined,
) => runtimeStatus === "STATUS$ERROR";

export const isConversationCompleted = (hasPr: boolean) => hasPr;

export const isConversationOpeningPR = (
  conversationStatus: ConversationStatus | null | undefined,
  runtimeStatus: RuntimeStatus | null | undefined,
) => conversationStatus === "RUNNING" && runtimeStatus === "STATUS$READY";
