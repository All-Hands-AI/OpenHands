import { extractNextPageFromLink } from "#/utils/extract-next-page-from-link";
import { github } from "./github-axios-instance";

const handleRequest = async <T>(requestFn: () => Promise<T>): Promise<T> => {
  try {
    return await requestFn();
  } catch (error) {
    throw error;
  }
};

const handleTokenRefresh = async (
  refreshToken: () => Promise<boolean>,
  logout: () => void,
): Promise<boolean> => {
  try {
    const refreshed = await refreshToken();
    if (!refreshed) {
      logout();
      throw new Error("Token refresh failed. User logged out.");
    }
    return true;
  } catch (error) {
    logout();
    throw new Error("Token refresh failed. User logged out.");
  }
};

const handleErrorResponse = (error: any): GitHubErrorReponse => {
  console.error("GitHub API request failed:", error);
  return {
    message: error.message || "An unknown error occurred",
    documentation_url: "",
    status: error?.response?.status || 500,
  };
};

/**
 * Retry for expired Github token
 * @param requestFn The Github API request function
 * @param refreshToken Function to issue refresh token
 * @param logout Function to logout user for expired token
 * @returns The headers for the GitHub API
 */
export const githubAPIRequest = async <T>(
  requestFn: () => Promise<T>,
  refreshToken: () => Promise<boolean>,
  logout: () => void,
): Promise<T | GitHubErrorReponse> => {
  try {
    return await handleRequest(requestFn);
  } catch (error: any) {
    if (error?.response?.status === 401 || error?.response?.status === 403) {
      try {
        await handleTokenRefresh(refreshToken, logout);
        return await handleRequest(requestFn); // Retry after successful token refresh
      } catch (refreshError) {
        return handleErrorResponse(refreshError);
      }
    } else {
      return handleErrorResponse(error);
    }
  }
};

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

export const retrieveGitHubAppInstallations = async (
  token: string,
  refreshToken: () => Promise<boolean>,
  logout: () => void,
): Promise<number[] | GitHubErrorReponse> => {
  const response = await github.get<{ installations: { id: number }[] }>(
    "/user/installations",
    {
      params: {},
      transformResponse: (data: string) => {
        const parsedData:
          | { installations: { id: number } }
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
    transformResponse: (data: string) => {
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
