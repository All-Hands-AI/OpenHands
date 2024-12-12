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
  const parts = url.replace("https://github.com/", "").split("/");
  return parts.length === 2 ? parts : [];
};
