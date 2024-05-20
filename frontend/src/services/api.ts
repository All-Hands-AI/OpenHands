import { getToken } from "./auth";
import toast from "#/utils/toast";

const WAIT_FOR_AUTH_DELAY_MS = 500;

export async function request(
  url: string,
  optionsIn: RequestInit = {},
  disableToast: boolean = false
  /* eslint-disable-next-line @typescript-eslint/no-explicit-any */
): Promise<any> {
  const options = JSON.parse(JSON.stringify(optionsIn));

  const needsAuth = !url.startsWith("/api/options/");
  const token = getToken();
  if (!token && needsAuth) {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(request(url, optionsIn));
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
    if (!disableToast) {
      toast.error("api", `${response.status} error while fetching ${url}: ${response.statusText}`);
    }
    throw new Error(response.statusText);
  }
  if (!response.ok) {
    if (!disableToast) {
      toast.error("api", "Error fetching " + url);
    }
    throw new Error(response.statusText);
  }
  return response.json();
}
