import axios from "axios";

export const openHands = axios.create();

// Add response interceptor to handle auth errors
openHands.interceptors.response.use(
  (response) => response,
  (error) => {
    // If it's an auth error (401 or 403) and we have a window object (we're in a browser)
    if (
      error.response?.status === 401 || 
      error.response?.status === 403
    ) {
      // Don't redirect if we're already on the auth endpoint
      if (!error.config.url?.includes('/api/authenticate')) {
        // Get the current URL to save it for later
        const currentPath = window.location.pathname + window.location.search;
        // Save the current page to localStorage if we're not on the home page
        if (currentPath !== '/') {
          import('../utils/last-page').then(({ saveLastPage }) => {
            saveLastPage();
          });
        }
        // Get the GitHub auth URL and redirect
        import('../hooks/use-github-auth-url').then(({ getGitHubAuthUrl }) => {
          const url = getGitHubAuthUrl();
          if (url) {
            window.location.href = url;
          }
        });
      }
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
