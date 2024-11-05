import OpenHands from "#/api/open-hands";

export const userIsAuthenticated = async () => {
  console.log("is auth");
  console.log(new Error().stack);
  if (window.__APP_MODE__ === "oss") return true;

  try {
    await OpenHands.authenticate();
    return true;
  } catch (error) {
    return false;
  }
};
