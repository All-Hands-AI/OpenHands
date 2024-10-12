/**
 * Get the valid fallback host. Returns the host unless it is localhost, in which case it returns localhost:3000
 * @returns Valid fallback host
 *
 * @example
 * // If the host is localhost (e.g., localhost:5173), it returns localhost:3000
 * const host = getValidFallbackHost(); // localhost:3000
 *
 * // If the host is not localhost, it returns the host
 * const host = getValidFallbackHost(); // sub.example.com
 */
export const getValidFallbackHost = () => {
  if (typeof window !== "undefined") {
    const { hostname, host } = window.location;
    if (hostname !== "localhost") return host;
  }

  // Fallback is localhost:3000 because that is the default port for the server
  return "localhost:3000";
};
