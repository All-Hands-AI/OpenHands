const getCachedConfig = (): { [key: string]: string } => {
  const config = localStorage.getItem("ALL_SETTINGS");
  if (config === null || config === undefined) return {};
  try {
    return JSON.parse(config);
  } catch (e) {
    return {};
  }
};

export { getCachedConfig };
