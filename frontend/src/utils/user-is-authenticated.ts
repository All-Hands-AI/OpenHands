import OpenHands from "#/api/open-hands";
import { cache } from "./cache";

export const userIsAuthenticated = async () => {
  if (window.__APP_MODE__ === "oss") return true;

  const cachedData = cache.get<boolean>("user_is_authenticated");
  if (cachedData) return cachedData;

  let authenticated = false;
  try {
    await OpenHands.authenticate();
    authenticated = true;
  } catch (error) {
    authenticated = false;
  }

  cache.set("user_is_authenticated", authenticated, 3 * 60 * 1000); // cache for 3 minutes
  return authenticated;
};
