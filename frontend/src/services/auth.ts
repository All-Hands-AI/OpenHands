const TOKEN_KEY = "token";
const GITHUB_TOKEN_KEY = "ghToken";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const getGitHubToken = () => localStorage.getItem(GITHUB_TOKEN_KEY);
