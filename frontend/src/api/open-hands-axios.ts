import usePersistStore from "#/zutand-stores/persist-config/usePersistStore";
import axios, { InternalAxiosRequestConfig } from "axios";

// Temporary fix to test CORS
const baseURL = `${window.location.protocol}//${import.meta.env.VITE_BACKEND_BASE_URL || window?.location.host}`;

export const openHands = axios.create({
  baseURL,
  headers: {
    "Cache-Control": "no-cache",
    "Content-Type": "application/json",
  },
});

// Request interceptor
openHands.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Check for JWT in store
    const token = usePersistStore.getState().jwt;
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// // Response interceptor
// openHands.interceptors.response.use(
//   (response) => {
//     return response;
//   },
//   (error) => {
//     if (error.response) {
//       switch (error.response.status) {
//         case 401:
//           break;
//         case 403:
//           break;
//         case 404:
//           break;
//         case 500:
//           break;
//       }
//     }
//     return Promise.reject(error);
//   },
// );

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
