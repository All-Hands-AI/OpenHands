import axios, { AxiosError } from "axios";

const github = axios.create({
  baseURL: "https://api.github.com",
  headers: {
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
  },
});

const setAuthTokenHeader = (token: string) => {
  github.defaults.headers.common.Authorization = `Bearer ${token}`;
};

const removeAuthTokenHeader = () => {
  if (github.defaults.headers.common.Authorization) {
    delete github.defaults.headers.common.Authorization;
  }
};

/**
 * Checks if response has attributes to perform refresh
 */
const canRefresh = (error: unknown): boolean =>
  !!(
    error instanceof AxiosError &&
    error.config &&
    error.response &&
    error.response.status
  );

/**
 * Checks if the data is a GitHub error response
 * @param data The data to check
 * @returns Boolean indicating if the data is a GitHub error response
 */
export const isGitHubErrorReponse = <T extends object | Array<unknown>>(
  data: T | GitHubErrorReponse | null,
): data is GitHubErrorReponse =>
  !!data && "message" in data && data.message !== undefined;

// Axios interceptor to handle token refresh
const setupAxiosInterceptors = (
  refreshToken: () => Promise<boolean>,
  logout: () => void,
) => {
  github.interceptors.response.use(
    // Pass successful responses through
    (response) => {
      const parsedData = response.data;
      if (isGitHubErrorReponse(parsedData)) {
        const error = new AxiosError(
          "Failed",
          "",
          response.config,
          response.request,
          response,
        );
        throw error;
      }
      return response;
    },
    // Retry request exactly once if token is expired
    async (error) => {
      if (!canRefresh(error)) {
        return Promise.reject(new Error("Failed to refresh token"));
      }

      const originalRequest = error.config;

      // Check if the error is due to an expired token
      if (
        error.response.status === 401 &&
        !originalRequest._retry // Prevent infinite retry loops
      ) {
        originalRequest._retry = true;
        try {
          const refreshed = await refreshToken();
          if (refreshed) {
            return await github(originalRequest);
          }

          logout();
          return await Promise.reject(new Error("Failed to refresh token"));
        } catch (refreshError) {
          // If token refresh fails, evict the user
          logout();
          return Promise.reject(refreshError);
        }
      }

      // If the error is not due to an expired token, propagate the error
      return Promise.reject(error);
    },
  );
};

export {
  github,
  setAuthTokenHeader,
  removeAuthTokenHeader,
  setupAxiosInterceptors,
};
