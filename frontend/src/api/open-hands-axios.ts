import axios from "axios";

export const openHands = axios.create({
  baseURL: `${window.location.protocol}//${import.meta.env.VITE_BACKEND_BASE_URL || window?.location.host}`,
});
export const setAuthTokenHeader = (token: string) => {
  openHands.defaults.headers.common.Authorization = `Bearer ${token}`;
};

export const removeAuthTokenHeader = () => {
  if (openHands.defaults.headers.common.Authorization) {
    delete openHands.defaults.headers.common.Authorization;
  }
};
