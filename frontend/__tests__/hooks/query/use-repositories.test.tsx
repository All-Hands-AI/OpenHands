import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

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
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
        staleTime: 0,
      },
    },
  });
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <AuthProvider initialToken="test-token">{children}</AuthProvider>
    </QueryClientProvider>
  );

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient.clear();
    vi.mocked(useConfig).mockReturnValue({ data: { APP_MODE: "oss" } });
    vi.mocked(useAppInstallations).mockReturnValue({ data: [1, 2] });
    vi.mocked(retrieveGitHubUserRepositories).mockResolvedValue({
      data: [],
      nextPage: null,
    });
    vi.mocked(retrieveGitHubAppRepositories).mockResolvedValue({
      data: { repositories: [] },
      nextPage: null,
      installationIndex: null,
    });
  });

  afterEach(() => {
    queryClient.clear();
  });

  describe("useUserRepositories", () => {
    it("should request 1000 repositories per page", async () => {
      vi.mocked(retrieveGitHubUserRepositories).mockResolvedValueOnce({
        data: [],
        nextPage: null,
      });

      const { result } = renderHook(() => useUserRepositories(), { wrapper });

      // Wait for the query to be enabled and executed
      await waitFor(() => {
        expect(result.current.isEnabled).toBe(true);
      }, { timeout: 3000 });

      await waitFor(() => {
        expect(retrieveGitHubUserRepositories).toHaveBeenCalledWith(1, 1000);
      }, { timeout: 3000 });
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

      const { result } = renderHook(() => useAppRepositories(), { wrapper });

      // Wait for the query to be enabled and executed
      await waitFor(() => {
        expect(result.current.isEnabled).toBe(true);
      }, { timeout: 3000 });

      await waitFor(() => {
        expect(retrieveGitHubAppRepositories).toHaveBeenCalledWith(0, [1, 2], 1, 1000);
      }, { timeout: 3000 });
    });
  });
});
