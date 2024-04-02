import * as jose from "jose";

const fetchToken = async (): Promise<string> => {
  const response = await fetch(`/api/auth`);
  if (response.status !== 200) {
    throw new Error("Get token failed.");
  }
  const data = await response.json();
  if (data.token === undefined || data.token === "") {
    throw new Error("Get token failed.");
  }
  return data.token;
};

const validateToken = (token: string): boolean => {
  try {
    const claims = jose.decodeJwt(token);
    const exp = claims.exp ?? 0;
    if (exp === 0) {
      localStorage.removeItem("token");
      return false;
    }
    if (exp > Date.now() / 1000) {
      return true;
    }
  } catch (error) {
    return false;
  }
  return false;
};

const getToken = async (): Promise<string> => {
  const token = localStorage.getItem("token") ?? "";
  if (validateToken(token)) {
    return token;
  }

  const newToken = await fetchToken();
  if (validateToken(newToken)) {
    localStorage.setItem("token", newToken);
    return newToken;
  }
  throw new Error("Token validation failed.");
};

export { getToken };
