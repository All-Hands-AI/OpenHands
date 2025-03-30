/**
 * Generates a URL to redirect to for GitHub OAuth
 * @param clientId The GitHub OAuth client ID
 * @param requestUrl The URL of the request
 * @param offline True for offline session, defaults to false
 * @returns The URL to redirect to for GitHub OAuth
 */
export const generateGitHubAuthUrl = (clientId: string, requestUrl: URL) => {
  const redirectUri = `${requestUrl.origin}/oauth/keycloak/callback`;
  const authUrl = requestUrl.hostname
    .replace(/(^|\.)staging\.all-hands\.dev$/, "$1auth.staging.all-hands.dev")
    .replace(/(^|\.)app\.all-hands\.dev$/, "auth.app.all-hands.dev")
    .replace(/(^|\.)localhost$/, "auth.staging.all-hands.dev");
  const scope = "openid email profile";
  return `https://${authUrl}/realms/allhands/protocol/openid-connect/auth?client_id=github&response_type=code&redirect_uri=${encodeURIComponent(redirectUri)}&scope=${encodeURIComponent(scope)}`;
};
