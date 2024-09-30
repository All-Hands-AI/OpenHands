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
  per_page = 30,
  page = 1,
): Promise<Response> => {
  const url = new URL("https://api.github.com/user/repos");
  url.searchParams.append("sort", "pushed"); // sort by most recently pushed
  url.searchParams.append("per_page", per_page.toString());
  url.searchParams.append("page", page.toString());

  return fetch(url.toString(), {
    headers: generateGitHubAPIHeaders(token),
  });
};

/**
 * Given a GitHub token, retrieves all repositories of the authenticated user
 * @param token The GitHub token
 * @returns A list of repositories or an error response
 */
export const retrieveAllGitHubUserRepositories = async (
  token: string,
): Promise<GitHubRepository[] | GitHubErrorReponse> => {
  const repositories: GitHubRepository[] = [];

  // Fetch the first page to extract the last page number and get the first batch of data
  const firstPageResponse = await retrieveGitHubUserRepositories(token, 100, 1);

  if (!firstPageResponse.ok) {
    return {
      message: "Failed to fetch repositories",
      documentation_url:
        "https://docs.github.com/rest/reference/repos#list-repositories-for-the-authenticated-user",
      status: firstPageResponse.status,
    };
  }

  const firstPageData = await firstPageResponse.json();
  repositories.push(...firstPageData);

  // Check for pagination and extract the last page number
  const link = firstPageResponse.headers.get("link");
  const lastPageMatch = link?.match(/page=(\d+)>; rel="last"/);
  const lastPage = lastPageMatch ? parseInt(lastPageMatch[1], 10) : 1;

  // If there is only one page, return the fetched repositories
  if (lastPage === 1) {
    return repositories;
  }

  // Create an array of promises for the remaining pages
  const promises = [];
  for (let page = 2; page <= lastPage; page += 1) {
    promises.push(retrieveGitHubUserRepositories(token, 100, page));
  }

  // Fetch all pages in parallel
  const responses = await Promise.all(promises);

  for (const response of responses) {
    if (response.ok) {
      // TODO: Is there a way to avoid using await within a loop?
      // eslint-disable-next-line no-await-in-loop
      const data = await response.json();
      repositories.push(...data);
    } else {
      return {
        message: "Failed to fetch repositories",
        documentation_url:
          "https://docs.github.com/rest/reference/repos#list-repositories-for-the-authenticated-user",
        status: response.status,
      };
    }
  }

  return repositories;
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
  const data = await response.json();

  if (!isGitHubErrorReponse(data)) {
    // Only return the necessary user data
    const user: GitHubUser = {
      id: data.id,
      login: data.login,
      avatar_url: data.avatar_url,
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

export const retrieveLatestGitHubCommit = async (
  token: string,
  repository: string,
): Promise<GitHubCommit[] | GitHubErrorReponse> => {
  const url = new URL(`https://api.github.com/repos/${repository}/commits`);
  url.searchParams.append("per_page", "1");
  const response = await fetch(url.toString(), {
    headers: generateGitHubAPIHeaders(token),
  });

  return response.json();
};
