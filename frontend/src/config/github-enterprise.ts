/**
 * GitHub Enterprise Server configuration
 */

/**
 * Initialize GitHub Enterprise Server configuration from environment variables
 */
export const initGitHubEnterpriseConfig = () => {
  // Set GitHub Enterprise URL if available
  if (import.meta.env.VITE_GITHUB_ENTERPRISE_URL) {
    window.GITHUB_ENTERPRISE_URL = import.meta.env.VITE_GITHUB_ENTERPRISE_URL;
  }

  // Set GitHub API URL if available
  if (import.meta.env.VITE_GITHUB_API_URL) {
    window.GITHUB_API_URL = import.meta.env.VITE_GITHUB_API_URL;
  }

  // Set GitHub Web URL if available
  if (import.meta.env.VITE_GITHUB_WEB_URL) {
    window.GITHUB_WEB_URL = import.meta.env.VITE_GITHUB_WEB_URL;
  }
};
