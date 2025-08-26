import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi, describe, it, beforeEach, expect } from "vitest";
import { GitBranchDropdown } from "#/components/features/home/git-branch-dropdown/git-branch-dropdown";
import { Branch } from "#/types/git";
import { Provider } from "#/types/settings";

// Mock the API
vi.mock("#/api/open-hands", () => ({
  default: {
    getRepositoryBranches: vi.fn(),
    searchRepositoryBranches: vi.fn(),
  },
}));

// Mock react-i18next
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

const mockBranches: Branch[] = [
  {
    name: "main",
    commit_sha: "abc123def456",
    protected: true,
    last_push_date: "2024-01-15T10:30:00Z",
  },
  {
    name: "develop",
    commit_sha: "def456ghi789",
    protected: false,
    last_push_date: "2024-01-14T15:45:00Z",
  },
  {
    name: "feature/new-component",
    commit_sha: "ghi789jkl012",
    protected: false,
    last_push_date: "2024-01-13T09:20:00Z",
  },
];

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe("GitBranchDropdown", () => {
  const defaultProps = {
    repository: "owner/repo",
    provider: "github" as Provider,
    selectedBranch: null,
    onBranchSelect: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders with placeholder when no branch is selected", () => {
    render(<GitBranchDropdown {...defaultProps} />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByPlaceholderText("REPOSITORY$SELECT_BRANCH")).toBeInTheDocument();
  });

  it("shows selected branch name when branch is selected", () => {
    const selectedBranch = mockBranches[0];
    render(
      <GitBranchDropdown {...defaultProps} selectedBranch={selectedBranch} />,
      {
        wrapper: createWrapper(),
      }
    );

    expect(screen.getByDisplayValue("main")).toBeInTheDocument();
  });

  it("is disabled when no repository is provided", () => {
    render(
      <GitBranchDropdown {...defaultProps} repository={null} />,
      {
        wrapper: createWrapper(),
      }
    );

    const input = screen.getByPlaceholderText("REPOSITORY$SELECT_BRANCH");
    expect(input).toBeDisabled();
  });

  it("is disabled when disabled prop is true", () => {
    render(
      <GitBranchDropdown {...defaultProps} disabled={true} />,
      {
        wrapper: createWrapper(),
      }
    );

    const input = screen.getByPlaceholderText("REPOSITORY$SELECT_BRANCH");
    expect(input).toBeDisabled();
  });

  it("calls onBranchSelect when clear button is clicked", async () => {
    const onBranchSelect = vi.fn();
    const selectedBranch = mockBranches[0];

    render(
      <GitBranchDropdown
        {...defaultProps}
        selectedBranch={selectedBranch}
        onBranchSelect={onBranchSelect}
      />,
      {
        wrapper: createWrapper(),
      }
    );

    const clearButton = screen.getByRole("button", { name: /clear/i });
    fireEvent.click(clearButton);

    expect(onBranchSelect).toHaveBeenCalledWith(null);
  });

  it("opens dropdown when input is focused", async () => {
    render(<GitBranchDropdown {...defaultProps} />, {
      wrapper: createWrapper(),
    });

    const input = screen.getByPlaceholderText("REPOSITORY$SELECT_BRANCH");
    fireEvent.focus(input);

    await waitFor(() => {
      expect(screen.getByRole("listbox")).toBeInTheDocument();
    });
  });

  it("updates input value when typing", () => {
    render(<GitBranchDropdown {...defaultProps} />, {
      wrapper: createWrapper(),
    });

    const input = screen.getByPlaceholderText("REPOSITORY$SELECT_BRANCH");
    fireEvent.change(input, { target: { value: "feature" } });

    expect(input).toHaveValue("feature");
  });

  it("uses custom placeholder when provided", () => {
    const customPlaceholder = "Choose a branch";
    render(
      <GitBranchDropdown {...defaultProps} placeholder={customPlaceholder} />,
      {
        wrapper: createWrapper(),
      }
    );

    expect(screen.getByPlaceholderText(customPlaceholder)).toBeInTheDocument();
  });
});