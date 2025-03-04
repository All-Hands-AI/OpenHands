/**
 * Generates a URL to redirect to for GitHub OAuth
 * @param clientId The GitHub OAuth client ID
 * @param requestUrl The URL of the request
 * @param offline True for offline session, defaults to false
 * @returns The URL to redirect to for GitHub OAuth
 */
export const generateGitHubAuthUrl = (
  clientId: string,
  requestUrl: URL,
  offline: boolean = false,
) => {
  const redirectUri = offline
    ? `http://localhost:3000/oauth/keycloak/offline/callback`
    : `http://localhost:3000/oauth/keycloak/callback`;

  const authUrl = requestUrl.hostname
    .replace(/(^|\.)staging\.all-hands\.dev$/, "$1auth.staging.all-hands.dev")
    .replace(/(^|\.)app\.all-hands\.dev$/, "auth.app.all-hands.dev")
    .replace(/(^|\.)localhost$/, "auth.staging.all-hands.dev");

  const scope = offline
    ? "openid email profile offline_access"
    : "openid email profile";

  return `http://127.0.0.1:8080/realms/allhands/protocol/openid-connect/auth?client_id=github&response_type=code&redirect_uri=${encodeURIComponent(redirectUri)}&scope=${encodeURIComponent(scope)}`;
};
