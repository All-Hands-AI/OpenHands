const TOKEN_KEY = "token";

const getToken = (): string => localStorage.getItem(TOKEN_KEY) ?? "";

const clearToken = (): void => {
  localStorage.removeItem(TOKEN_KEY);
};

const setToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token);
};

export { getToken, setToken, clearToken };
