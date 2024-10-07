import { createCookieSessionStorage } from "@remix-run/node";
import { Settings } from "./services/settings";

type SessionData = {
  tosAccepted: boolean;
  ghToken: string;
  token: string; // Session token
};

export const { getSession, commitSession, destroySession } =
  createCookieSessionStorage<SessionData>({
    cookie: {
      name: "__session",
      secrets: ["some_secret"],
    },
  });

type SettingsSessionData = { settings: Settings };

export const {
  getSession: getSettingsSession,
  commitSession: commitSettingsSession,
  destroySession: destroySettingsSession,
} = createCookieSessionStorage<SettingsSessionData>({
  cookie: {
    name: "__settings",
    secrets: ["some_other_secret"],
  },
});
