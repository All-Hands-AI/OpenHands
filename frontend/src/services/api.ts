import { getToken } from "./auth";

const WAIT_FOR_AUTH_DELAY_MS = 500;

export async function request(
  url: string,
  options: RequestInit = {},
): Promise<any> {
  const token = getToken();
  if (!token)
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        resolve(request(url, options));
      }, WAIT_FOR_AUTH_DELAY_MS);
    });
  options.headers = {
    ...(options.headers || {}),
    Authorization: `Bearer ${token}`,
  };
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(response.statusText);
  }
  if (response.status >= 400) {
    throw new Error(response.statusText);
  }
  return response.json();
}
