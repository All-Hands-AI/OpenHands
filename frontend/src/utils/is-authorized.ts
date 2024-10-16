import { retrieveGitHubUser, isGitHubErrorReponse } from "#/api/github";

type WaitlistUser = {
  handle: string;
};

/**
 * Check if the user is authorized. For now this is used in the SaaS mode to check if the user is in the waitlist.
 * @param ghToken The GitHub token
 * @returns A boolean indicating if the user is authorized
 */
export const isAuthorized = async (isSaas: boolean, ghToken: string | null) => {
  let waitlist: { users: WaitlistUser[] } = { users: [] };

  try {
    // @ts-expect-error - This is temporary, file may not exist
    waitlist = await import("#/../public/waitlist.json");
  } catch (e) {
    // pass
  }

  if (isSaas) {
    let user: GitHubUser | GitHubErrorReponse | null = null;
    if (ghToken) user = await retrieveGitHubUser(ghToken);

    if (!isGitHubErrorReponse(user)) {
      const inWaitlist = waitlist.users.find((u) => u.handle === user?.login);
      return inWaitlist;
    }

    return false;
  }

  return true;
};
