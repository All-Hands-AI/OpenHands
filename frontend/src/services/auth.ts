const TOKEN_KEY = "token";
const GITHUB_TOKEN_KEY = "ghToken";

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

export {
  getToken,
  setToken,
  clearToken,
  getGitHubToken,
  setGitHubToken,
  clearGitHubToken,
};
