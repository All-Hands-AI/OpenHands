import axios from "axios";
import { saveLastPage } from "#/utils/last-page";

export const openHands = axios.create({
  baseURL: `${window.location.protocol}//${import.meta.env.VITE_BACKEND_BASE_URL || window?.location.host}`,
});

// Add response interceptor to handle 401 and 403 errors
openHands.interceptors.response.use(
  (response) => response,
  (error) => {
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
