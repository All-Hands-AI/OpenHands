import { createCookieSessionStorage } from "@remix-run/node";

type SessionData = {
  tosAccepted: boolean;
  ghToken: string;
};

const { getSession, commitSession, destroySession } =
  createCookieSessionStorage<SessionData>({
    cookie: {
      name: "__session",
      secrets: ["some_secret"],
    },
  });

export { getSession, commitSession, destroySession };
