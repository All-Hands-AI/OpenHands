import axios from "axios";
import { handleLogoutAndRefresh } from "#/utils/auth-utils";

export const openHands = axios.create({
  baseURL: `${window.location.protocol}//${import.meta.env.VITE_BACKEND_BASE_URL || window?.location.host}`,
});

// Add response interceptor to handle 401 Unauthorized responses
openHands.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Check if the error is a 401 Unauthorized
    if (error.response && error.response.status === 401) {
      // Get app mode from localStorage or default to "oss"
      const appMode = localStorage.getItem("appMode") || "oss";

      // Only handle logout and refresh for "saas" mode
      if (appMode === "saas") {
        await handleLogoutAndRefresh(appMode);
      }
    }

    // Return the original error for other error handling
    return Promise.reject(error);
  },
);
