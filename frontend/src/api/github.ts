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

/**
 * Checks if the data is a GitHub error response
 * @param data The data to check
 * @returns Boolean indicating if the data is a GitHub error response
 */
export const isGitHubErrorReponse = <T extends object | Array<unknown>>(
  data: T | GitHubErrorReponse | null,
): data is GitHubErrorReponse =>
  !!data && "message" in data && data.message !== undefined;

export const retrieveGitHubAppInstallations = async (
  token: string,
): Promise<string[]> => {
  const installationsUrl = "https://api.github.com/user/installations";

  const installationsResponse = await fetch(installationsUrl, {
    headers: generateGitHubAPIHeaders(token),
  });

  if (!installationsResponse.ok) {
    throw new Error(
      `Failed to fetch installations: ${installationsResponse.statusText}`,
    );
  }

  const installationsData = await installationsResponse.json();
  const installationIds = installationsData.installations.map(
    (installation: { id: number }) => installation.id,
  );

  return installationIds;
};

/**
 * Given a GitHub token, retrieves the repositories of the authenticated user
 * @param token The GitHub token
 * @returns A list of repositories or an error response
 */
export const retrieveGitHubUserRepositories = async (
  gitHubToken: string,
  page = 1,
  per_page = 30,
): Promise<Response> => {
  const baseUrl = window.location.origin;
  const url = new URL("/api/github/repositories", baseUrl);
  url.searchParams.append("sort", "pushed");
  url.searchParams.append("page", page.toString());
  url.searchParams.append("per_page", per_page.toString());

  return fetch(url.toString(), {
    headers: {
      "X-GitHub-Token": gitHubToken,
    },
  });
};

/**
 * Given a GitHub token, retrieves the authenticated user
 * @param token The GitHub token
 * @returns The authenticated user or an error response
 */
export const retrieveGitHubUser = async (
  token: string,
): Promise<GitHubUser | GitHubErrorReponse> => {
  const response = await fetch("https://api.github.com/user", {
    headers: generateGitHubAPIHeaders(token),
  });

  if (!response.ok) {
    throw new Error("Failed to retrieve user data");
  }

  const data = await response.json();

  if (!isGitHubErrorReponse(data)) {
    // Only return the necessary user data
    const user: GitHubUser = {
      id: data.id,
      login: data.login,
      avatar_url: data.avatar_url,
      company: data.company,
      name: data.name,
      email: data.email,
    };

    return user;
  }

  const error: GitHubErrorReponse = {
    message: data.message,
    documentation_url: data.documentation_url,
    status: response.status,
  };

  return error;
};

export const retrieveLatestGitHubCommit = async (
  token: string,
  repository: string,
): Promise<GitHubCommit[] | GitHubErrorReponse> => {
  const url = new URL(`https://api.github.com/repos/${repository}/commits`);
  url.searchParams.append("per_page", "1");
  const response = await fetch(url.toString(), {
    headers: generateGitHubAPIHeaders(token),
  });

  if (!response.ok) {
    throw new Error("Failed to retrieve latest commit");
  }

  return response.json();
};
