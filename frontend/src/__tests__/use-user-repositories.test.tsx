import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { AuthProvider } from "../context/auth-context";
import { useUserRepositories } from "../hooks/query/use-user-repositories";

// Mock the auth context
vi.mock("../context/auth-context", () => ({
  useAuth: () => ({
    gitHubToken: "mock-token",
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
}));

// Mock the config hook
vi.mock("../hooks/query/use-config", () => ({
  useConfig: () => ({
    data: {
      APP_MODE: "oss",
    },
  }),
}));

// Mock the GitHub API response
vi.mock("../api/github", () => ({
  retrieveGitHubUserRepositories: vi.fn().mockImplementation((page) => {
    const repos = Array.from({ length: 100 }, (_, i) => ({
      id: i + (page - 1) * 100,
      full_name: `repo-${i + (page - 1) * 100}`,
    }));
    return Promise.resolve({
      data: repos,
      nextPage: page < 3 ? page + 1 : undefined,
    });
  }),
}));

const store = configureStore({
  reducer: {
    initialQuery: (state = {}) => state,
  },
});

describe("useUserRepositories", () => {
  it("should fetch all repositories with pagination", async () => {
    const queryClient = new QueryClient();
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        <Provider store={store}>
          <AuthProvider>{children}</AuthProvider>
        </Provider>
      </QueryClientProvider>
    );

    const { result } = renderHook(() => useUserRepositories(), { wrapper });

    // Wait for all pages to be fetched
    await waitFor(() => {
      expect(result.current.data?.pages.length).toBe(3);
    });

    // Check that we have all repositories
    const allRepos = result.current.data?.pages.flatMap((page) => page.data) ?? [];
    expect(allRepos.length).toBe(300); // 3 pages * 100 repos per page
  });
});
