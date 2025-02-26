/**
 * Generates a URL to redirect to for GitHub OAuth
 * @param clientId The GitHub OAuth client ID
 * @param requestUrl The URL of the request
 * @returns The URL to redirect to for GitHub OAuth
 */
export const generateGitHubAuthUrl = (clientId: string, requestUrl: URL) => {
  const redirectUri = `${requestUrl.origin}/oauth/github/callback`;
  const baseUrl = `${requestUrl.origin}`
    .replace("https://", "")
    .replace("http://", "");
  const authUrl = baseUrl
    .replace(/(^|\.)staging\.all-hands\.dev$/, ".auth.staging.all-hands.dev")
    .replace(/(^|\.)app\.all-hands\.dev$/, "auth.app.all-hands.dev");
  const scope = "openid email profile";
  const force_build = true;
  return `https://${authUrl}/realms/allhands/protocol/openid-connect/auth?client_id=github&response_type=code&redirect_uri=${encodeURIComponent(redirectUri)}&scope=${encodeURIComponent(scope)}&state=some-state-value&nonce=222`;
};
