import { describe, it, expect } from "vitest";
import { extractNextPageFromLink } from "../../utils/extract-next-page-from-link";

describe("extractNextPageFromLink", () => {
  it("should extract next page number from GitHub API link header", () => {
    const link =
      '<https://api.github.com/user/repos?page=2>; rel="next", <https://api.github.com/user/repos?page=3>; rel="last"';
    expect(extractNextPageFromLink(link)).toBe(2);
  });

  it("should return null when there is no next page", () => {
    const link =
      '<https://api.github.com/user/repos?page=1>; rel="first", <https://api.github.com/user/repos?page=3>; rel="last"';
    expect(extractNextPageFromLink(link)).toBe(null);
  });

  it("should handle empty link header", () => {
    expect(extractNextPageFromLink("")).toBe(null);
  });
});
