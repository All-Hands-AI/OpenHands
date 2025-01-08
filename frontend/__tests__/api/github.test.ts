import { describe, expect, it, vi } from "vitest";
import { retrieveLatestGitHubCommit } from "../../src/api/github";

describe("retrieveLatestGitHubCommit", () => {
  const { openHandsGetMock } = vi.hoisted(() => ({
    openHandsGetMock: vi.fn(),
  }));

  vi.mock("../../src/api/open-hands-axios", () => ({
    openHands: {
      get: openHandsGetMock,
    },
  }));

  it("should return the latest commit when repository has commits", async () => {
    const mockCommit = {
      sha: "123abc",
      commit: {
        message: "Initial commit",
      },
    };

    openHandsGetMock.mockResolvedValueOnce({
      data: [mockCommit],
    });

    const result = await retrieveLatestGitHubCommit("user/repo");
    expect(result).toEqual(mockCommit);
  });

  it("should return null when repository is empty", async () => {
    const error = new Error("Repository is empty");
    (error as any).response = { status: 409 };
    openHandsGetMock.mockRejectedValueOnce(error);

    const result = await retrieveLatestGitHubCommit("user/empty-repo");
    expect(result).toBeNull();
  });

  it("should throw error for other error cases", async () => {
    const error = new Error("Network error");
    (error as any).response = { status: 500 };
    openHandsGetMock.mockRejectedValueOnce(error);

    await expect(retrieveLatestGitHubCommit("user/repo")).rejects.toThrow();
  });
});
