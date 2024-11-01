import OpenHands from "#/api/open-hands";

export const userIsAuthenticated = async () => {
  try {
    await OpenHands.authenticate();
    return true;
  } catch (error) {
    return false;
  }
};
