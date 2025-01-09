/**
 * Generates a URL to redirect to for GitHub OAuth
 * @param clientId The GitHub OAuth client ID
 * @param requestUrl The URL of the request
 * @returns The URL to redirect to for GitHub OAuth
 */
export const generateGitHubAuthUrl = (clientId: string, requestUrl: URL) => {
  const redirectUri = `${requestUrl.origin}/oauth/github/callback`;
  // const redirectUri = `http://127.0.0.1:8000/callback`;
  const scope = "repo,user,workflow,offline_access";
  console.log("Client ID:", clientId)
  console.log("Request URL:", requestUrl)
  console.log("Redirect URL:", redirectUri)
  // return `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=${encodeURIComponent(scope)}`;
  return `http://localhost:8080/realms/allhandsgithub/protocol/openid-connect/auth?client_id=allhandsgithub&response_type=code&redirect_uri=${encodeURIComponent(redirectUri)}&scope=openid+email+profile&state=some-state-value&nonce=222`;
  // return `http://localhost:8080/realms/allhands/protocol/openid-connect/auth?client_id=test&response_type=code&redirect_uri=http://localhost:3001/api/keycloak/callback&scope=openid+email+profile&state=some-state-value&nonce=222`;
};
