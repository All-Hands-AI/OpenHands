import * as jose from "jose";

const getToken = (): string => {
  return localStorage.getItem("token") ?? "";
};

const clearToken = (): void => {
  localStorage.removeItem("token");
}

const setToken = (token: string): void => {
  localStorage.setItem("token", token);
}

export { getToken, setToken, clearToken };
