import OpenHands from "#/api/open-hands";

export const userIsAuthenticated = async (ghToken: string | null) => {
  if (window.__APP_MODE__ !== "saas") return true;
  if (!ghToken) return false;

  const authResponse = await OpenHands.authenticate(ghToken);
  return authResponse.ok;
};
