import posthog from "posthog-js";
import { describe, expect, it, vi } from "vitest";
import { logoutCleanup } from "#/utils/logout-cleanup";

describe("logoutCleanup", () => {
  it("should clear the GitHub token from local storage", () => {
    localStorage.setItem("ghToken", "test-token");
    logoutCleanup();

    expect(localStorage.getItem("ghToken")).toBeNull();
  });

  it("should reset posthog properties", () => {
    const resetSpy = vi.spyOn(posthog, "reset");
    logoutCleanup();

    expect(resetSpy).toHaveBeenCalled();
  });
});
