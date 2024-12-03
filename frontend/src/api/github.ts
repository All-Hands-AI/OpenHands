import { extractNextPageFromLink } from "#/utils/extract-next-page-from-link";
import { github } from "./github-axios-instance";

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
 * Given a GitHub token, retrieves the repositories of the authenticated user
 * @param token The GitHub token
 * @returns A list of repositories or an error response
 */
export const retrieveGitHubUserRepositories = async (
  page = 1,
  per_page = 30,
) => {
  const response = await github.get<GitHubRepository[]>("/user/repos", {
    params: {
      sort: "pushed",
      page,
      per_page,
    },
    transformResponse: (data) => {
      const parsedData: GitHubRepository[] | GitHubErrorReponse =
        JSON.parse(data);

      if (isGitHubErrorReponse(parsedData)) {
        throw new Error(parsedData.message);
      }

      return parsedData;
    },
  });

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
    transformResponse: (data) => {
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
      transformResponse: (data) => {
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
