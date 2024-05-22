import { getToken } from "./auth";
import toast from "#/utils/toast";

const WAIT_FOR_AUTH_DELAY_MS = 500;

export async function request(
  url: string,
  optionsIn: RequestInit = {},
  disableToast: boolean = false,
  /* eslint-disable-next-line @typescript-eslint/no-explicit-any */
): Promise<any> {
  const options = JSON.parse(JSON.stringify(optionsIn));

  const onFail = (msg: string) => {
    if (!disableToast) {
      toast.error("api", msg);
    }
    throw new Error(msg);
  };

  const needsAuth = !url.startsWith("/api/options/");
  const token = getToken();
  if (!token && needsAuth) {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(request(url, optionsIn, disableToast));
      }, WAIT_FOR_AUTH_DELAY_MS);
    });
  }
  if (token) {
    options.headers = {
      ...(options.headers || {}),
      Authorization: `Bearer ${token}`,
    };
  }

  let response = null;
  try {
    response = await fetch(url, options);
  } catch (e) {
    onFail(`Error fetching ${url}`);
  }
  if (response?.status && response?.status >= 400) {
    onFail(
      `${response.status} error while fetching ${url}: ${response?.statusText}`,
    );
  }
  if (!response?.ok) {
    onFail(`Error fetching ${url}: ${response?.statusText}`);
  }

  try {
    return await (response && response.json());
  } catch (e) {
    onFail(`Error parsing JSON from ${url}`);
  }
  return null;
}
