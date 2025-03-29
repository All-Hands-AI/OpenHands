import { expect, test, beforeEach, afterEach } from "vitest";
import { parseGithubUrl } from "../../src/utils/parse-github-url";

// Save original window properties
const originalWindow = { ...window };

beforeEach(() => {
  // Reset window properties before each test
  window.GITHUB_WEB_URL = undefined;
});

afterEach(() => {
  // Restore window properties after each test
  window.GITHUB_WEB_URL = originalWindow.GITHUB_WEB_URL;
});

test("parseGithubUrl with github.com", () => {
  expect(
    parseGithubUrl("https://github.com/alexreardon/tiny-invariant"),
  ).toEqual(["alexreardon", "tiny-invariant"]);

  expect(parseGithubUrl("https://github.com/All-Hands-AI/OpenHands")).toEqual([
    "All-Hands-AI",
    "OpenHands",
  ]);

  expect(parseGithubUrl("https://github.com/All-Hands-AI/")).toEqual([
    "All-Hands-AI",
    "",
  ]);

  expect(parseGithubUrl("https://github.com/")).toEqual([]);
});

test("parseGithubUrl with GitHub Enterprise Server", () => {
  // Set GitHub Enterprise Server URL
  window.GITHUB_WEB_URL = "https://github.example.com";

  expect(
    parseGithubUrl("https://github.example.com/alexreardon/tiny-invariant"),
  ).toEqual(["alexreardon", "tiny-invariant"]);

  expect(parseGithubUrl("https://github.example.com/All-Hands-AI/OpenHands")).toEqual([
    "All-Hands-AI",
    "OpenHands",
  ]);

  expect(parseGithubUrl("https://github.example.com/All-Hands-AI/")).toEqual([
    "All-Hands-AI",
    "",
  ]);

  expect(parseGithubUrl("https://github.example.com/")).toEqual([]);

  // Test with different domain
  window.GITHUB_WEB_URL = "https://git.company.com";

  expect(
    parseGithubUrl("https://git.company.com/alexreardon/tiny-invariant"),
  ).toEqual(["alexreardon", "tiny-invariant"]);
});
