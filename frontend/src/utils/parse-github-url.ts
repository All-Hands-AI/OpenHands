/**
 * Given a GitHub URL of a repository, obtain the owner and repository name
 * @param url The GitHub repository URL
 * @returns An array containing the owner and repository names
 *
 * @example
 * const parsed = parseGithubUrl("https://github.com/All-Hands-AI/OpenHands");
 * console.log(parsed) // ["All-Hands-AI", "OpenHands"]
 */
export const parseGithubUrl = (url: string) => {
  // Get the GitHub web URL (default or enterprise)
  const githubWebUrl = window.GITHUB_WEB_URL || "https://github.com";

  // Remove the base URL and extract owner/repo
  const repoPath = url
    .replace(`${githubWebUrl}/`, "")
    .replace(/^https?:\/\/[^/]+\//, "");
  const parts = repoPath.split("/");

  return parts.length >= 2 ? [parts[0], parts[1]] : [];
};
