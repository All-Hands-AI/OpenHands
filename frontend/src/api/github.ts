import { extractNextPageFromLink } from "#/utils/extract-next-page-from-link";
import { github } from "./github-axios-instance";
import { openHands } from "./open-hands-axios";

/**
 * Retrieves GitHub app installations for the user
 */
export const retrieveGitHubAppInstallations = async (): Promise<
  number[] | GitHubErrorReponse
> => {
  const response = await github.get<GithubAppInstallation>(
    "/user/installations",
  );

  return response.data.installations.map(
    (installation: { id: number }) => installation.id,
  );
};

/**
 * Given a GitHub token, retrieves the repositories of the authenticated user
 * @param token The GitHub token
 * @returns A list of repositories or an error response
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
 * Given a GitHub token, retrieves the repositories of the authenticated user
 * @param token The GitHub token
 * @returns A list of repositories or an error response
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
 * @param token The GitHub token
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

export const retrieveLatestGitHubCommit = async (
  repository: string,
): Promise<GitHubCommit> => {
  const response = await github.get<GitHubCommit[]>(
    `/repos/${repository}/commits`,
    {
      params: {
        per_page: 1,
      },
    },
  );

  return response.data[0];
};
