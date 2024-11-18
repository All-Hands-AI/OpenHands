/**
 * Extracts the next page number from a GitHub API link header.
 * @param link The GitHub API link header
 * @returns The next page number or null if there is no next page
 */
export const extractNextPageFromLink = (link: string): number | null => {
  const match = link.match(/<.*\?page=(\d+)>; rel="next"/);
  return match ? parseInt(match[1], 10) : null;
};
