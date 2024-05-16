const getToken = (): string => localStorage.getItem("token") ?? "";

const clearToken = (): void => {
  localStorage.removeItem("token");
};

const setToken = (token: string): void => {
  localStorage.setItem("token", token);
};

export { getToken, setToken, clearToken };
