import { retrieveGitHubUser, isGitHubErrorReponse } from "#/api/github";
import OpenHands from "#/api/open-hands";

export const userIsAuthenticated = async (ghToken: string | null) => {
  if (window.__APP_MODE__ !== "saas") return true;

  let user: GitHubUser | GitHubErrorReponse | null = null;
  if (ghToken) user = await retrieveGitHubUser(ghToken);

  if (user && !isGitHubErrorReponse(user)) {
    const isAuthed = await OpenHands.isAuthenticated(user.login);
    return isAuthed;
  }

  return false;
};
