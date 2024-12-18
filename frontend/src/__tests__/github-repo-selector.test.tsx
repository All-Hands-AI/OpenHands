import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { AuthProvider } from "../context/auth-context";
import { GitHubRepositorySelector } from "../components/features/github/github-repo-selector";

vi.mock("../hooks/query/use-config", () => ({
  useConfig: () => ({
    data: {
      APP_MODE: "oss",
    },
  }),
}));

const store = configureStore({
  reducer: {
    initialQuery: (state = {}) => state,
  },
});

const queryClient = new QueryClient();

describe("GitHubRepositorySelector", () => {
  const mockRepositories = Array.from({ length: 50 }, (_, i) => ({
    id: i,
    full_name: `repo-${i}`,
  }));

  it("should render all repositories", () => {
    // Mock localStorage
    const localStorageMock = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    };
    Object.defineProperty(window, "localStorage", { value: localStorageMock });

    render(
      <QueryClientProvider client={queryClient}>
        <Provider store={store}>
          <AuthProvider>
            <GitHubRepositorySelector
              onSelect={() => {}}
              repositories={mockRepositories}
            />
          </AuthProvider>
        </Provider>
      </QueryClientProvider>
    );

    // Open the dropdown by typing
    const input = screen.getByRole("combobox");
    fireEvent.change(input, { target: { value: "repo" } });

    // Check if all repositories are rendered
    const items = screen.getAllByTestId("github-repo-item");
    expect(items).toHaveLength(50);
  });
});
