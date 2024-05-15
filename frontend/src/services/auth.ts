import * as jose from "jose";

export const validateToken = (token: string): boolean => {
  try {
    const claims = jose.decodeJwt(token);
    return !(claims.sid === undefined || claims.sid === "");
  } catch (error) {
    return false;
  }
};

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
