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
  data: T | GitHubErrorReponse | null,
): data is GitHubErrorReponse =>
  !!data && "message" in data && data.message !== undefined;

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

/**
 * Given a GitHub token and a repository name, creates a repository for the authenticated user
 * @param token The GitHub token
 * @param repositoryName Name of the repository to create
 * @param description Description of the repository
 * @param isPrivate Boolean indicating if the repository should be private
 * @returns The created repository or an error response
 */
export const createGitHubRepository = async (
  token: string,
  repositoryName: string,
  description?: string,
  isPrivate = true,
): Promise<GitHubRepository | GitHubErrorReponse> => {
  const response = await fetch("https://api.github.com/user/repos", {
    method: "POST",
    headers: generateGitHubAPIHeaders(token),
    body: JSON.stringify({
      name: repositoryName,
      description,
      private: isPrivate,
    }),
  });

  return response.json();
};
