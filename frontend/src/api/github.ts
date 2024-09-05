interface GitHubErrorReponse {
  message: string;
  documentation_url: string;
  status: number;
}

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
  data: T | GitHubErrorReponse,
): data is GitHubErrorReponse =>
  "message" in data && data.message !== undefined;

/**
 * Given a GitHub token, retrieves the repositories of the authenticated user
 * @param token The GitHub token
 * @returns A list of repositories or an error response
 */
export const retrieveGitHubUserRepositories = async (
  token: string,
): Promise<GitHubRepository[] | GitHubErrorReponse> => {
  const response = await fetch("https://api.github.com/user/repos", {
    headers: generateGitHubAPIHeaders(token),
  });

  return response.json();
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

  return response.json();
};
