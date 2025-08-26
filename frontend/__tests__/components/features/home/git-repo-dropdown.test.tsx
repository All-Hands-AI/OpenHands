import React from "react";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { GitRepoDropdown } from "#/components/features/home/git-repo-dropdown";
import { describe, it, expect } from "vitest";

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe("GitRepoDropdown", () => {
  it("renders without crashing", () => {
    render(
      <TestWrapper>
        <GitRepoDropdown
          provider="github"
          value={null}
          onChange={() => {}}
        />
      </TestWrapper>
    );

    const input = screen.getByTestId("git-repo-dropdown");
    expect(input).toBeInTheDocument();
  });

  it("shows placeholder text when no repository is selected", () => {
    render(
      <TestWrapper>
        <GitRepoDropdown
          provider="github"
          value={null}
          onChange={() => {}}
        />
      </TestWrapper>
    );

    const input = screen.getByPlaceholderText("Search repositories...");
    expect(input).toBeInTheDocument();
  });
});