import OpenHands from "#/api/open-hands";

export const userIsAuthenticated = async () => {
  if (window.__APP_MODE__ === "oss") return true;

  try {
    await OpenHands.authenticate();
    return true;
  } catch (error) {
    return false;
  }
};
