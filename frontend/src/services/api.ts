import { getToken, getGitHubToken } from "./auth";
import toast from "#/utils/toast";

const WAIT_FOR_AUTH_DELAY_MS = 500;

const UNAUTHED_ROUTE_PREFIXES = [
  "/api/authenticate",
  "/api/options/",
  "/config.json",
  "/api/github/callback",
];

export async function request(
  url: string,
  options: RequestInit = {},
  disableToast: boolean = false,
  returnResponse: boolean = false,
  maxRetries: number = 3,
  /* eslint-disable-next-line @typescript-eslint/no-explicit-any */
): Promise<any> {
  if (maxRetries < 0) {
    throw new Error("Max retries exceeded");
  }
  const onFail = (msg: string) => {
    if (!disableToast) {
      toast.error("api", msg);
    }
    throw new Error(msg);
  };

  const needsAuth = !UNAUTHED_ROUTE_PREFIXES.some((prefix) =>
    url.startsWith(prefix),
  );
  const token = getToken();
  const githubToken = getGitHubToken();
  if (!token && needsAuth) {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(
          request(url, options, disableToast, returnResponse, maxRetries - 1),
        );
      }, WAIT_FOR_AUTH_DELAY_MS);
    });
  }
  if (token) {
    // eslint-disable-next-line no-param-reassign
    options.headers = {
      ...(options.headers || {}),
      Authorization: `Bearer ${token}`,
    };
  }
  if (githubToken) {
    // eslint-disable-next-line no-param-reassign
    options.headers = {
      ...(options.headers || {}),
      "X-GitHub-Token": githubToken,
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

  if (returnResponse) {
    return response;
  }

  try {
    return await (response && response.json());
  } catch (e) {
    onFail(`Error parsing JSON from ${url}`);
  }
  return null;
}
