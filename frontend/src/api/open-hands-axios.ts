import axios from "axios";
import { saveLastPage } from "#/utils/last-page";

export const openHands = axios.create();

// Add response interceptor to handle 401 errors
openHands.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Save the last page before redirecting
      saveLastPage();
    }
    return Promise.reject(error);
  }
);

export const setAuthTokenHeader = (token: string) => {
  openHands.defaults.headers.common.Authorization = `Bearer ${token}`;
};

export const setGitHubTokenHeader = (token: string) => {
  openHands.defaults.headers.common["X-GitHub-Token"] = token;
};

export const removeAuthTokenHeader = () => {
  if (openHands.defaults.headers.common.Authorization) {
    delete openHands.defaults.headers.common.Authorization;
  }
};

export const removeGitHubTokenHeader = () => {
  if (openHands.defaults.headers.common["X-GitHub-Token"]) {
    delete openHands.defaults.headers.common["X-GitHub-Token"];
  }
};
