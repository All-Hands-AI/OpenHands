import axios, { AxiosError } from "axios";
import { KeycloakErrorResponse } from "./open-hands.types";

export const openHands = axios.create();

export const setAuthTokenHeader = (token: string) => {
  console.log(`setAuthTokenHeader to ${token}`)
  openHands.defaults.headers.common.Authorization = `Bearer ${token}`;
};

export const setGitHubTokenHeader = (token: string) => {
  console.log(`setGitHubTokenHeader to ${token}`)
  openHands.defaults.headers.common["X-GitHub-Token"] = token;
};

export const removeAuthTokenHeader = () => {
  console.log("removeAuthTokenHeader")
  if (openHands.defaults.headers.common.Authorization) {
    delete openHands.defaults.headers.common.Authorization;
  }
};

export const removeGitHubTokenHeader = () => {
  console.log("removeGitHubTokenHeader")
  if (openHands.defaults.headers.common["X-GitHub-Token"]) {
    delete openHands.defaults.headers.common["X-GitHub-Token"];
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
    error.response.status &&
    error.response.data.keycloak_error
  );
/**
 * Checks if the data is a Keycloak error response
 * @param data The data to check
 * @returns Boolean indicating if the data is a Keycloak error response
 */
export const isKeycloakErrorResponse = <T extends object | Array<unknown>>(
  data: T | KeycloakErrorResponse | null,
): data is KeycloakErrorResponse =>
  !!data && "keycloak_error" in data;

// Axios interceptor to handle token refresh
export const setupOpenhandsAxiosInterceptors = (
  refreshToken: () => Promise<boolean>,
  logout: () => void,
) => {
  openHands.interceptors.response.use(
    // Pass successful responses through
    (response) => {
      const parsedData = response.data;
      console.log("Openhands API call response:")
      console.log(parsedData)
      if (isKeycloakErrorResponse(parsedData)) {
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
            originalRequest.headers["X-GitHub-Token"] = openHands.defaults.headers.common["X-GitHub-Token"]
            return await openHands(originalRequest);
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
