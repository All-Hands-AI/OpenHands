import posthog from "posthog-js";

/**
 * Clears the GitHub token from local storage and resets PostHog properties.
 */
export const logoutCleanup = () => {
  localStorage.removeItem("ghToken");
  posthog.reset();
};
