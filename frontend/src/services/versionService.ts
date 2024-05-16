/**
 * Service to fetch the backend version from the API endpoint.
 */
const getBackendVersion = async (): Promise<string> => {
  try {
    const response = await fetch('/api/version');
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    const data = await response.json();
    return data.version;
  } catch (error) {
    console.error('Error fetching backend version:', error);
    throw error;
  }
};

export { getBackendVersion };
