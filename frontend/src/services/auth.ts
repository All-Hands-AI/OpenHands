import * as jose from "jose";
import { ResFetchToken } from "../types/ResponseType";

const fetchToken = async (): Promise<ResFetchToken> => {
  const headers = new Headers({
    "Content-Type": "application/json",
    Authorization: `Bearer ${localStorage.getItem("token")}`,
  });
  const response = await fetch(`/api/auth`, { headers });
  if (response.status !== 200) {
    throw new Error("Get token failed.");
  }
  const data: ResFetchToken = await response.json();
  return data;
};

const validateToken = (token: string): boolean => {
  try {
    const claims = jose.decodeJwt(token);
    return !(claims.sid === undefined || claims.sid === "");
  } catch (error) {
    return false;
  }
};

const getToken = async (): Promise<string> => {
  const token = localStorage.getItem("token") ?? "";
  if (validateToken(token)) {
    return token;
  }

  const data = await fetchToken();
  if (data.token === undefined || data.token === "") {
    throw new Error("Get token failed.");
  }
  const newToken = data.token;
  if (validateToken(newToken)) {
    localStorage.setItem("token", newToken);
    return newToken;
  }
  throw new Error("Token validation failed.");
};

export { getToken, fetchToken };
