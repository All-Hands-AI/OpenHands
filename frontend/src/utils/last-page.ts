const LAST_PAGE_KEY = "openhands_last_page";

export const saveLastPage = () => {
  const currentPath = window.location.pathname;
  // Don't save login/settings pages
  if (!currentPath.includes("/settings") && currentPath !== "/") {
    localStorage.setItem(LAST_PAGE_KEY, currentPath);
  }
};

export const getLastPage = (): string | null =>
  localStorage.getItem(LAST_PAGE_KEY);

export const clearLastPage = () => {
  localStorage.removeItem(LAST_PAGE_KEY);
};
