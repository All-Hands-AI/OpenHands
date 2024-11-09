import posthog from "posthog-js";
import { cache } from "#/utils/cache";

import OpenHands from "#/api/open-hands";

const TOKEN_KEY = "token";
const GITHUB_TOKEN_KEY = "ghToken";
const REPO_KEY = "repo"

const getToken = (): string => localStorage.getItem(TOKEN_KEY) ?? "";

const clearToken = (): void => {
  localStorage.removeItem(TOKEN_KEY);
};

const setToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token);
};

const getGitHubToken = (): string =>
  localStorage.getItem(GITHUB_TOKEN_KEY) ?? "";

const setGitHubToken = (token: string): void => {
  localStorage.setItem(GITHUB_TOKEN_KEY, token);
};

const clearGitHubToken = (): void => {
  localStorage.removeItem(GITHUB_TOKEN_KEY);
};

const logout = (): void => {
  clearToken();
  clearGitHubToken();
  localStorage.removeItem(REPO_KEY);
  cache.clearAll();
  posthog.reset();
  OpenHands.logout();
}

export {
  getToken,
  setToken,
  clearToken,
  getGitHubToken,
  setGitHubToken,
  clearGitHubToken,
  logout,
};
