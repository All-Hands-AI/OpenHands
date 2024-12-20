/**
 * Generates a URL to redirect to for GitHub OAuth
 * @param clientId The GitHub OAuth client ID
 * @param requestUrl The URL of the request
 * @returns The URL to redirect to for GitHub OAuth
 */
export const generateGitHubAuthUrl = (clientId: string, requestUrl: URL) => {
  const redirectUri = `${requestUrl.origin}/oauth/github/callback`;
  const scope = "repo,user,workflow,offline_access";
  return `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=${encodeURIComponent(scope)}`;
};
