import * as jose from "jose";

const parseJwt = (token: string): { [key: string]: string } => {
  try {
    return jose.decodeJwt(token);
  } catch (e) {
    return {};
  }
};

export { parseJwt };
