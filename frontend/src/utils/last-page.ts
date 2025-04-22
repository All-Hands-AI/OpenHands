const LAST_PAGE_KEY = "openhandsLastPage";

export const saveLastPage = () => {
  const currentPath = window.location.pathname;
  // Don't save root, tos, or settings pages
  if (
    !currentPath.includes("/settings") &&
    currentPath !== "/" &&
    currentPath !== "/tos"
  ) {
    localStorage.setItem(LAST_PAGE_KEY, currentPath);
  } else if (currentPath === "/" && window.location.search) {
    // If we're on the root page but have query parameters, save the full URL
    localStorage.setItem(
      LAST_PAGE_KEY,
      window.location.pathname + window.location.search,
    );
  }
};

export const getLastPage = (): string | null =>
  localStorage.getItem(LAST_PAGE_KEY);

export const clearLastPage = () => {
  localStorage.removeItem(LAST_PAGE_KEY);
};
