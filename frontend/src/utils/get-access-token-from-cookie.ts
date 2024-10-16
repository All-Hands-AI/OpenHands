export const getAccessTokenFromCookie = (cookie: string) =>
  cookie?.match(/access_token=([^;]*)/)?.[1] || null;
