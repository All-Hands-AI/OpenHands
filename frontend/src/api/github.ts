/**
 * Generates the headers for the GitHub API
 * @param token The GitHub token
 * @returns The headers for the GitHub API
 */
const generateGitHubAPIHeaders = (token: string) =>
  ({
    Accept: "application/vnd.github+json",
    Authorization: `Bearer ${token}`,
    "X-GitHub-Api-Version": "2022-11-28",
  }) as const;

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
): Promise<string[] | GitHubErrorReponse> => {
  return githubAPIRequest(
    async () => {
      const response = await fetch(
        "https://api.github.com/user/installations",
        {
          headers: generateGitHubAPIHeaders(token),
        },
      );
      if (!response.ok) {
        throw {
          response: { status: response.status },
          message: "Failed to fetch installations",
        };
      }
      const data = await response.json();
      return data.installations.map(
        (installation: { id: number }) => installation.id,
      );
    },
    refreshToken,
    logout,
  );
};

/**
 * Given a GitHub token, retrieves the repositories of the authenticated user
 * @param token The GitHub token
 * @returns A list of repositories or an error response
 */
export const retrieveGitHubUserRepositories = async (
  token: string,
  refreshToken: () => Promise<boolean>,
  logout: () => void,
  page = 1,
  per_page = 30,
  installationId: string | null = null,
): Promise<Response | GitHubErrorReponse> => {
  return githubAPIRequest(
    async () => {
      const baseUrl = window.location.origin;
      const url = new URL("/api/github/repositories", baseUrl);
      url.searchParams.append("sort", "pushed");
      url.searchParams.append("page", page.toString());
      url.searchParams.append("per_page", per_page.toString());

      if (installationId) {
        url.searchParams.append("installation_id", installationId);
      }

      const response = await fetch(url.toString(), {
        headers: generateGitHubAPIHeaders(token),
      });
      if (!response.ok) {
        throw {
          response: { status: response.status },
          message: "Failed to retrieve repositories",
        };
      }
      return response.json();
    },
    refreshToken,
    logout,
  );
};

/**
 * Given a GitHub token, retrieves the authenticated user
 * @param token The GitHub token
 * @returns The authenticated user or an error response
 */
export const retrieveGitHubUser = async (
  token: string,
  refreshToken: () => Promise<boolean>,
  logout: () => void,
): Promise<GitHubUser | GitHubErrorReponse> => {
  return githubAPIRequest(
    async () => {
      const response = await fetch("https://api.github.com/user", {
        headers: generateGitHubAPIHeaders(token),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw {
          message: errorData.message || "Failed to retrieve user data",
          response: { status: response.status },
        };
      }

      const data = await response.json();

      return {
        id: data.id,
        login: data.login,
        avatar_url: data.avatar_url,
        company: data.company,
        name: data.name,
        email: data.email,
      } as GitHubUser;
    },
    refreshToken,
    logout,
  );
};

export const retrieveLatestGitHubCommit = async (
  token: string,
  refreshToken: () => Promise<boolean>,
  logout: () => void,
  repository: string,
): Promise<GitHubCommit[] | GitHubErrorReponse> => {
  return githubAPIRequest(
    async () => {
      const url = new URL(`https://api.github.com/repos/${repository}/commits`);
      url.searchParams.append("per_page", "1");
      const response = await fetch(url.toString(), {
        headers: generateGitHubAPIHeaders(token),
      });
      if (!response.ok) {
        throw {
          response: { status: response.status },
          message: "Failed to retrieve latest commit",
        };
      }
      return response.json();
    },
    refreshToken,
    logout,
  );
};
