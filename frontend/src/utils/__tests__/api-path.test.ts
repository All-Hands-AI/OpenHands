import { describe, it, expect } from "vitest";
import { getApiPath } from "../api-path";

describe("getApiPath", () => {
  it("should not modify paths when APP_MODE is not 'saas'", () => {
    expect(getApiPath("/api/user/info", "oss")).toBe("/api/user/info");
    expect(getApiPath("/api/user/repositories", null)).toBe("/api/user/repositories");
    expect(getApiPath("/api/user", undefined)).toBe("/api/user");
  });

  it("should modify paths when APP_MODE is 'saas'", () => {
    expect(getApiPath("/api/user/info", "saas")).toBe("/api/user/saas/info");
    expect(getApiPath("/api/user/repositories", "saas")).toBe("/api/user/saas/repositories");
    expect(getApiPath("/api/user/search/repositories", "saas")).toBe("/api/user/saas/search/repositories");
    expect(getApiPath("/api/user/repository/branches", "saas")).toBe("/api/user/saas/repository/branches");
    expect(getApiPath("/api/user/suggested-tasks", "saas")).toBe("/api/user/saas/suggested-tasks");
  });

  it("should handle root user path correctly", () => {
    expect(getApiPath("/api/user", "saas")).toBe("/api/user/saas");
    expect(getApiPath("/api/user/", "saas")).toBe("/api/user/saas");
  });

  it("should not modify non-user API paths", () => {
    expect(getApiPath("/api/conversations", "saas")).toBe("/api/conversations");
    expect(getApiPath("/api/settings", "saas")).toBe("/api/settings");
    expect(getApiPath("/api/options/models", "saas")).toBe("/api/options/models");
  });
});
