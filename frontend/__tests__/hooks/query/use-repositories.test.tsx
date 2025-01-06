import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("#/api/github", () => ({
  retrieveGitHubUserRepositories: vi.fn(),
  retrieveGitHubAppRepositories: vi.fn(),
}));

vi.mock("#/hooks/query/use-config", () => ({
  useConfig: vi.fn(),
}));

vi.mock("#/hooks/query/use-app-installations", () => ({
  useAppInstallations: vi.fn(),
}));

import { renderHook, waitFor } from "@testing-library/react";
import { useUserRepositories } from "#/hooks/query/use-user-repositories";
import { useAppRepositories } from "#/hooks/query/use-app-repositories";
import { retrieveGitHubUserRepositories, retrieveGitHubAppRepositories } from "#/api/github";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "#/context/auth-context";
import { useConfig } from "#/hooks/query/use-config";
import { useAppInstallations } from "#/hooks/query/use-app-installations";

describe("Repository Loading Hooks", () => {
  const queryClient = new QueryClient();
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <AuthProvider initialToken="test-token">{children}</AuthProvider>
    </QueryClientProvider>
  );

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useConfig).mockReturnValue({ data: { APP_MODE: "oss" } });
    vi.mocked(useAppInstallations).mockReturnValue({ data: [1, 2] });
  });

  describe("useUserRepositories", () => {
    it("should request 1000 repositories per page", async () => {
      vi.mocked(retrieveGitHubUserRepositories).mockResolvedValueOnce({
        data: [],
        nextPage: null,
      });

      renderHook(() => useUserRepositories(), { wrapper });

      await waitFor(() => {
        expect(retrieveGitHubUserRepositories).toHaveBeenCalledWith(1, 1000);
      });
    });
  });

  describe("useAppRepositories", () => {
    beforeEach(() => {
      vi.mocked(useConfig).mockReturnValue({ data: { APP_MODE: "saas" } });
    });

    it("should request 1000 repositories per page", async () => {
      vi.mocked(retrieveGitHubAppRepositories).mockResolvedValueOnce({
        data: { repositories: [] },
        nextPage: null,
        installationIndex: null,
      });

      renderHook(() => useAppRepositories(), { wrapper });

      await waitFor(() => {
        expect(mockRetrieveGitHubAppRepositories).toHaveBeenCalledWith(0, [1, 2], 1, 1000);
      });
    });
  });
});
