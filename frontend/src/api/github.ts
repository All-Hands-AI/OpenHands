import { extractNextPageFromLink } from "#/utils/extract-next-page-from-link";
import { github } from "./github-axios-instance";
import { openHands } from "./open-hands-axios";

/**
 * Given the user, retrieves app installations IDs for OpenHands Github App
 * Uses user access token for Github App
 */
export const retrieveGitHubAppInstallations = async (): Promise<number[]> => {
  const response = await github.get<GithubAppInstallation>(
    "/user/installations",
  );

  return response.data.installations.map((installation) => installation.id);
};

/**
 * Retrieves repositories where OpenHands Github App has been installed
 * @param installationIndex Pagination cursor position for app installation IDs
 * @param installations Collection of all App installation IDs for OpenHands Github App
 * @returns A list of repositories
 */
export const retrieveGitHubAppRepositories = async (
  installationIndex: number,
  installations: number[],
  page = 1,
  per_page = 30,
) => {
  const installationId = installations[installationIndex];
  const response = await openHands.get<GitHubAppRepository>(
    "/api/github/repositories",
    {
      params: {
        sort: "pushed",
        page,
        per_page,
        installation_id: installationId,
      },
    },
  );

  const link = response.headers.link ?? "";
  const nextPage = extractNextPageFromLink(link);
  let nextInstallation: number | null;

  if (nextPage) {
    nextInstallation = installationIndex;
  } else if (installationIndex + 1 < installations.length) {
    nextInstallation = installationIndex + 1;
  } else {
    nextInstallation = null;
  }

  return {
    data: response.data.repositories,
    nextPage,
    installationIndex: nextInstallation,
  };
};

/**
 * Given a PAT, retrieves the repositories of the user
 * @returns A list of repositories
 */
export const retrieveGitHubUserRepositories = async (
  page = 1,
  per_page = 30,
) => {
  const response = await openHands.get<GitHubRepository[]>(
    "/api/github/repositories",
    {
      params: {
        sort: "pushed",
        page,
        per_page,
      },
    },
  );

  const link = response.headers.link ?? "";
  const nextPage = extractNextPageFromLink(link);

  return { data: response.data, nextPage };
};

/**
 * Given a GitHub token, retrieves the authenticated user
 * @returns The authenticated user or an error response
 */
export const retrieveGitHubUser = async () => {
  const response = await github.get<GitHubUser>("/user");

  const { data } = response;

  const user: GitHubUser = {
    id: data.id,
    login: data.login,
    avatar_url: data.avatar_url,
    company: data.company,
    name: data.name,
    email: data.email,
  };

  return user;
};

export const searchPublicRepositories = async (
  query: string,
  per_page = 5,
  sort: "" | "updated" | "stars" | "forks" = "stars",
  order: "desc" | "asc" = "desc",
): Promise<GitHubRepository[]> => {
  const response = await github.get<{ items: GitHubRepository[] }>(
    "/search/repositories",
    {
      params: {
        q: query,
        per_page,
        sort,
        order,
      },
    },
  );
  return response.data.items;
};

export const retrieveLatestGitHubCommit = async (
  repository: string,
): Promise<GitHubCommit | null> => {
  try {
    const response = await github.get<GitHubCommit[]>(
      `/repos/${repository}/commits`,
      {
        params: {
          per_page: 1,
        },
      },
    );
    return response.data[0] || null;
  } catch (error) {
    if (!error || typeof error !== "object") {
      throw new Error("Unknown error occurred");
    }
    const axiosError = error as { response?: { status: number } };
    if (axiosError.response?.status === 409) {
      // Repository is empty, no commits yet
      return null;
    }
    throw new Error(
      error instanceof Error ? error.message : "Unknown error occurred",
    );
  }
};
