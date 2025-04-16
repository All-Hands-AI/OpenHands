import axios from "axios";
import { saveLastPage } from "#/utils/last-page";

export const openHands = axios.create({
  baseURL: `${window.location.protocol}//${import.meta.env.VITE_BACKEND_BASE_URL || window?.location.host}`,
});

// Add request interceptor to block API calls when on TOS page
openHands.interceptors.request.use(
  (config) => {
    // If we're on the TOS page, block all API calls except for the TOS-specific ones
    if (window.location.pathname === "/tos") {
      // Only allow the TOS-specific API calls
      if (config.url && !config.url.includes("/api/tos")) {
        // Cancel the request
        return {
          ...config,
          cancelToken: new axios.CancelToken((cancel) =>
            cancel(`API call blocked on TOS page: ${config.url}`),
          ),
        };
      }
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// Add response interceptor to handle 401 and 403 errors
openHands.interceptors.response.use(
  (response) => response,
  (error) => {
    // Don't process if the request was cancelled
    if (axios.isCancel(error)) {
      return Promise.reject(error);
    }

    if (error.response?.status === 401) {
      // Save the last page before redirecting
      saveLastPage();
    } else if (
      error.response?.status === 403 &&
      error.response?.data?.tos_not_accepted
    ) {
      // Save the last page before redirecting to TOS
      // Only redirect if we're not already on the TOS page
      if (window.location.pathname !== "/tos") {
        saveLastPage();
        window.location.href = "/tos";
      }
    }
    return Promise.reject(error);
  },
);
