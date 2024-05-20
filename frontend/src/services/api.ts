import { getToken } from "./auth";
import toast from "#/utils/toast";

const WAIT_FOR_AUTH_DELAY_MS = 500;

export async function request(
  url: string,
  options_in: RequestInit = {},
  /* eslint-disable-next-line @typescript-eslint/no-explicit-any */
): Promise<any> {
  const options = JSON.parse(JSON.stringify(options_in));

  const needsAuth = !url.startsWith("/api/options/");
  const token = getToken();
  if (!token && needsAuth) {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(request(url, options_in));
      }, WAIT_FOR_AUTH_DELAY_MS);
    });
  } else if (token) {
    options.headers = {
      ...(options.headers || {}),
      Authorization: `Bearer ${token}`,
    };
  }
  const response = await fetch(url, options);
  if (response.status && response.status >= 400) {
    toast.error("api", `${response.status} error while fetching ${url}: ${response.statusText}`);
    throw new Error(response.statusText);
  }
  if (!response.ok) {
    toast.error("api", "Error fetching " + url);
    throw new Error(response.statusText);
  }
  return response.json();
}
