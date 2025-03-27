import { expect, test, beforeEach, afterEach } from "vitest";
import { generateGitHubAuthUrl } from "../../src/utils/generate-github-auth-url";

// Save original window properties
const originalWindow = { ...window };

beforeEach(() => {
  // Reset window properties before each test
  window.GITHUB_ENTERPRISE_URL = undefined;
});

afterEach(() => {
  // Restore window properties after each test
  window.GITHUB_ENTERPRISE_URL = originalWindow.GITHUB_ENTERPRISE_URL;
});

test("generateGitHubAuthUrl with default Keycloak flow", () => {
  const clientId = "test-client-id";
  const requestUrl = new URL("https://app.all-hands.dev/some/path");
  
  const authUrl = generateGitHubAuthUrl(clientId, requestUrl);
  
  // Should use Keycloak auth URL
  expect(authUrl).toContain("auth.app.all-hands.dev");
  expect(authUrl).toContain("realms/allhands/protocol/openid-connect/auth");
  expect(authUrl).toContain("client_id=github");
  expect(authUrl).toContain("redirect_uri=https%3A%2F%2Fapp.all-hands.dev%2Foauth%2Fkeycloak%2Fcallback");
});

test("generateGitHubAuthUrl with localhost", () => {
  const clientId = "test-client-id";
  const requestUrl = new URL("http://localhost:3000/some/path");
  
  const authUrl = generateGitHubAuthUrl(clientId, requestUrl);
  
  // Should use staging auth URL for localhost
  expect(authUrl).toContain("auth.staging.all-hands.dev");
});

test("generateGitHubAuthUrl with GitHub Enterprise Server", () => {
  const clientId = "enterprise-client-id";
  const requestUrl = new URL("https://app.example.com/some/path");
  
  // Set GitHub Enterprise URL
  window.GITHUB_ENTERPRISE_URL = "https://github.example.com";
  
  const authUrl = generateGitHubAuthUrl(clientId, requestUrl);
  
  // Should use GitHub Enterprise auth URL
  expect(authUrl).toContain("https://github.example.com/login/oauth/authorize");
  expect(authUrl).toContain("client_id=enterprise-client-id");
  expect(authUrl).toContain("redirect_uri=https%3A%2F%2Fapp.example.com%2Foauth%2Fkeycloak%2Fcallback");
  expect(authUrl).toContain("scope=repo,user");
  
  // Should not use Keycloak
  expect(authUrl).not.toContain("realms/allhands");
});