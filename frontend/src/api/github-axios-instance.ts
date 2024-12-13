import axios from "axios";

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

export { github, setAuthTokenHeader, removeAuthTokenHeader };
