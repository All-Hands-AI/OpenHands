import { getToken } from "./auth";

const WAIT_FOR_AUTH_DELAY_MS = 500;

export async function request(
  url: string,
  options_in: RequestInit = {},
  /* eslint-disable-next-line @typescript-eslint/no-explicit-any */
): Promise<any> {
  const token = getToken();
  if (!token)
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(request(url, options_in));
      }, WAIT_FOR_AUTH_DELAY_MS);
    });
  const options = JSON.parse(JSON.stringify(options_in));
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
