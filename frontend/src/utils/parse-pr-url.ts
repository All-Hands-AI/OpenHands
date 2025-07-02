/**
 * Utility function to parse Pull Request URLs from text
 */

// Common PR URL patterns for different Git providers
const PR_URL_PATTERNS = [
  // GitHub: https://github.com/owner/repo/pull/123
  /https?:\/\/github\.com\/[^/\s]+\/[^/\s]+\/pull\/\d+/gi,
  // GitLab: https://gitlab.com/owner/repo/-/merge_requests/123
  /https?:\/\/gitlab\.com\/[^/\s]+\/[^/\s]+\/-\/merge_requests\/\d+/gi,
  // GitLab self-hosted: https://gitlab.example.com/owner/repo/-/merge_requests/123
  /https?:\/\/[^/\s]*gitlab[^/\s]*\/[^/\s]+\/[^/\s]+\/-\/merge_requests\/\d+/gi,
  // Bitbucket: https://bitbucket.org/owner/repo/pull-requests/123
  /https?:\/\/bitbucket\.org\/[^/\s]+\/[^/\s]+\/pull-requests\/\d+/gi,
  // Azure DevOps: https://dev.azure.com/org/project/_git/repo/pullrequest/123
  /https?:\/\/dev\.azure\.com\/[^/\s]+\/[^/\s]+\/_git\/[^/\s]+\/pullrequest\/\d+/gi,
  // Generic pattern for other providers that might use /pull/ or /pr/
  /https?:\/\/[^/\s]+\/[^/\s]+\/[^/\s]+\/(?:pull|pr)\/\d+/gi,
];

/**
 * Extracts PR URLs from a given text
 * @param text - The text to search for PR URLs
 * @returns Array of found PR URLs
 */
export function extractPRUrls(text: string): string[] {
  const urls: string[] = [];

  for (const pattern of PR_URL_PATTERNS) {
    const matches = text.match(pattern);
    if (matches) {
      urls.push(...matches);
    }
  }

  // Remove duplicates and return
  return [...new Set(urls)];
}

/**
 * Checks if the text contains any PR URLs
 * @param text - The text to check
 * @returns True if PR URLs are found, false otherwise
 */
export function containsPRUrl(text: string): boolean {
  return extractPRUrls(text).length > 0;
}

/**
 * Gets the first PR URL found in the text
 * @param text - The text to search
 * @returns The first PR URL found, or null if none found
 */
export function getFirstPRUrl(text: string): string | null {
  const urls = extractPRUrls(text);
  return urls.length > 0 ? urls[0] : null;
}
