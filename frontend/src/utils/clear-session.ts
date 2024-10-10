/**
 * Clear the session data from the local storage. This will remove the token and repo
 */
export const clearSession = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("repo");
};
