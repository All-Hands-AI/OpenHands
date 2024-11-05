import OpenHands from "#/api/open-hands";
import { authCache } from "./auth-cache";

export const userIsAuthenticated = async () => {
  if (window.__APP_MODE__ === "oss") return true;

  const token = localStorage.getItem("token");
  if (!token) return false;

  // Check cache first
  const cachedStatus = authCache.getAuthStatus(token);
  if (cachedStatus !== undefined) {
    return cachedStatus;
  }

  try {
    await OpenHands.authenticate();
    authCache.setAuthStatus(token, true);
    return true;
  } catch (error) {
    authCache.setAuthStatus(token, false);
    return false;
  }
};
