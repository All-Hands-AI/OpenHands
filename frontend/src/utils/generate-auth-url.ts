/**
 * Generates a URL to redirect to for OAuth authentication
 * @param identityProvider The identity provider to use (e.g., "github", "gitlab")
 * @param requestUrl The URL of the request
 * @returns The URL to redirect to for OAuth
 */
export const generateAuthUrl = (identityProvider: string, requestUrl: URL) => {
  const redirectUri = `${requestUrl.origin}/oauth/keycloak/callback`;
  let authUrl = requestUrl.hostname
    .replace(/(^|\.)staging\.all-hands\.dev$/, "$1auth.staging.all-hands.dev")
    .replace(/(^|\.)app\.all-hands\.dev$/, "auth.app.all-hands.dev")
    .replace(/(^|\.)localhost$/, "auth.staging.all-hands.dev");

  // If no replacements matched, prepend "auth." (excluding localhost)
  if (authUrl === requestUrl.hostname && requestUrl.hostname !== "localhost") {
    authUrl = `auth.${requestUrl.hostname}`;
  }
  const scope = "openid email profile"; // OAuth scope - not user-facing
  return `https://${authUrl}/realms/allhands/protocol/openid-connect/auth?client_id=allhands&kc_idp_hint=${identityProvider}&response_type=code&redirect_uri=${encodeURIComponent(redirectUri)}&scope=${encodeURIComponent(scope)}&state=${encodeURIComponent(requestUrl.href)}`;
};
