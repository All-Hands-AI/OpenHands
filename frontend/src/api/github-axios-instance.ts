import axios from "axios";
import { isGitHubErrorReponse } from "./github";

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

const canRefresh = (error: any) => {
  return error && error.config && error.response && error.response.status;
};

// Axios interceptor to handle token refresh
const setupAxiosInterceptors = (
  refreshToken: () => Promise<boolean>,
  logout: () => void,
) => {
  github.interceptors.response.use(
    (response) => {
      const parsedData = response.data;
      if (isGitHubErrorReponse(parsedData)) {
        throw response;
      }
      return response;
    }, // Pass successful responses through
    async (error) => {
      console.log(error);
      console.log(canRefresh(error));

      if (!canRefresh(error)) {
        return Promise.reject(error);
      }

      const originalRequest = error.config;

      console.log(originalRequest, error.response.status);

      // Check if the error is due to an expired token
      if (
        error.response.status === 401 &&
        !originalRequest._retry // Prevent infinite retry loops
      ) {
        originalRequest._retry = true;
        try {
          const refreshed = await refreshToken();
          if (refreshed) {
            return github(originalRequest);
          }

          logout();
          return Promise.reject("Failed to refresh token");
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
