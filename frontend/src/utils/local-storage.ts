// Local storage keys
export const LOCAL_STORAGE_KEYS = {
  LOGIN_METHOD: 'openhands_login_method',
  LAST_PAGE: 'openhands_last_page',
};

// Login methods
export enum LoginMethod {
  GITHUB = 'github',
  GITLAB = 'gitlab',
}

/**
 * Set the login method in local storage
 * @param method The login method (github or gitlab)
 */
export const setLoginMethod = (method: LoginMethod): void => {
  localStorage.setItem(LOCAL_STORAGE_KEYS.LOGIN_METHOD, method);
};

/**
 * Get the login method from local storage
 * @returns The login method or null if not set
 */
export const getLoginMethod = (): LoginMethod | null => {
  const method = localStorage.getItem(LOCAL_STORAGE_KEYS.LOGIN_METHOD);
  return method as LoginMethod | null;
};

/**
 * Set the last visited page in local storage
 * @param path The path of the last visited page
 */
export const setLastPage = (path: string): void => {
  localStorage.setItem(LOCAL_STORAGE_KEYS.LAST_PAGE, path);
};

/**
 * Get the last visited page from local storage
 * @returns The last visited page or null if not set
 */
export const getLastPage = (): string | null => {
  return localStorage.getItem(LOCAL_STORAGE_KEYS.LAST_PAGE);
};

/**
 * Clear login method and last page from local storage
 */
export const clearLoginData = (): void => {
  localStorage.removeItem(LOCAL_STORAGE_KEYS.LOGIN_METHOD);
  localStorage.removeItem(LOCAL_STORAGE_KEYS.LAST_PAGE);
};

/**
 * Check if the given path should be excluded from being saved as the last page
 * @param path The path to check
 * @returns True if the path should be excluded, false otherwise
 */
export const shouldExcludePath = (path: string): boolean => {
  // Exclude settings pages and root app URL
  return path.startsWith('/settings') || path === '/';
};