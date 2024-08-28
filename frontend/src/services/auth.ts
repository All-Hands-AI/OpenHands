const TOKEN_KEY = "token";

const getToken = () => localStorage.getItem(TOKEN_KEY);

const clearToken = () => {
  localStorage.removeItem(TOKEN_KEY);
};

const setToken = (token: string) => {
  localStorage.setItem(TOKEN_KEY, token);
};

export { getToken, setToken, clearToken };
