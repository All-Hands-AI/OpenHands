/**
 * Generates a URL to redirect to for GitHub OAuth
 * @param clientId The GitHub OAuth client ID
 * @param requestUrl The URL of the request
 * @returns The URL to redirect to for GitHub OAuth
 */
export const generateGitHubAuthUrl = (clientId: string, requestUrl: URL) => {
  const redirectUri = `${requestUrl.origin}/oauth/github/callback`;
  const scope = "repo,user,workflow,offline_access";
  return `http://localhost:8080/realms/allhands/protocol/openid-connect/auth?client_id=allhands&response_type=code&redirect_uri=${encodeURIComponent(redirectUri)}&scope=openid+email+profile&state=some-state-value&nonce=222`;
};
