import { extractNextPageFromLink } from "#/utils/extract-next-page-from-link";
import { github } from "./github-axios-instance";
import { openHands } from "./open-hands-axios";

/**
 * Checks if the data is a GitHub error response
 * @param data The data to check
 * @returns Boolean indicating if the data is a GitHub error response
 */
export const isGitHubErrorReponse = <T extends object | Array<unknown>>(
  data: T | GitHubErrorReponse | null,
): data is GitHubErrorReponse =>
  !!data && "message" in data && data.message !== undefined;

/**
 * Retrieves GitHub app installations for the user
 */

export const retrieveGitHubAppInstallations = async (): Promise<
  number[] | GitHubErrorReponse
> => {
  const response = await github.get<{ installations: { id: number }[] }>(
    "/user/installations",
    {
      params: {},
      transformResponse: (data: string) => {
        const parsedData:
          | { installations: { id: number }[] }
          | GitHubErrorReponse = JSON.parse(data);

        if (isGitHubErrorReponse(parsedData)) {
          throw new Error(parsedData.message);
        }

        return parsedData;
      },
    },
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
  page = 1,
  per_page = 30,
  installation_index: number,
  installations: number[],
) => {
  const installation_id = installations[installation_index];
  const response = await openHands.get<{ repositories: GitHubRepository[] }>(
    "/api/github/repositories",
    {
      params: {
        sort: "pushed",
        page,
        per_page,
        installation_id,
      },
      transformResponse: (data: string) => {
        const parsedData:
          | { repositories: GitHubRepository[] }
          | GitHubErrorReponse = JSON.parse(data);

        if (isGitHubErrorReponse(parsedData)) {
          throw new Error(parsedData.message);
        }

        return parsedData;
      },
    },
  );

  const link = response.headers.link ?? "";
  const nextPage = extractNextPageFromLink(link);
  const nextInstallation = nextPage
    ? installation_index
    : !nextPage && installation_index + 1 < installations.length
      ? installation_index + 1
      : null;

  return {
    data: response.data.repositories,
    nextPage,
    installation_index: nextInstallation,
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
      transformResponse: (data: string) => {
        const parsedData: GitHubRepository[] | GitHubErrorReponse =
          JSON.parse(data);

        if (isGitHubErrorReponse(parsedData)) {
          throw new Error(parsedData.message);
        }

        return parsedData;
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
  const response = await github.get<GitHubUser>("/user", {
    transformResponse: (data: string) => {
      const parsedData: GitHubUser | GitHubErrorReponse = JSON.parse(data);

      if (isGitHubErrorReponse(parsedData)) {
        throw new Error(parsedData.message);
      }

      return parsedData;
    },
  });

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
  const response = await github.get<GitHubCommit>(
    `/repos/${repository}/commits`,
    {
      params: {
        per_page: 1,
      },
      transformResponse: (data: string) => {
        const parsedData: GitHubCommit[] | GitHubErrorReponse =
          JSON.parse(data);

        if (isGitHubErrorReponse(parsedData)) {
          throw new Error(parsedData.message);
        }

        return parsedData[0];
      },
    },
  );

  return response.data;
};
