import { render, screen } from "@testing-library/react";
import { describe, test, expect, beforeEach, vi } from "vitest";
import { RepositorySelectionForm } from "./repo-selection-form";
import { useUserRepositories } from "#/hooks/query/use-user-repositories";
import { useCreateConversation } from "#/hooks/mutation/use-create-conversation";
import { useIsCreatingConversation } from "#/hooks/use-is-creating-conversation";

// Mock the hooks
vi.mock("#/hooks/query/use-user-repositories");
vi.mock("#/hooks/mutation/use-create-conversation");
vi.mock("#/hooks/use-is-creating-conversation");
vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

describe("RepositorySelectionForm", () => {
  const mockOnRepoSelection = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    // Default mock implementations
    (
      useUserRepositories as unknown as ReturnType<typeof vi.fn>
    ).mockReturnValue({
      data: { pages: [{ data: [] }] },
      isLoading: false,
      isError: false,
    });

    (
      useCreateConversation as unknown as ReturnType<typeof vi.fn>
    ).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isSuccess: false,
    });

    (
      useIsCreatingConversation as unknown as ReturnType<typeof vi.fn>
    ).mockReturnValue(false);
  });

  test("shows loading indicator when repositories are being fetched", async () => {
    // Mock loading state
    (
      useUserRepositories as unknown as ReturnType<typeof vi.fn>
    ).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    });

    render(<RepositorySelectionForm onRepoSelection={mockOnRepoSelection} />);

    // Check if loading indicator is displayed
    expect(screen.getByTestId("repo-dropdown-loading")).toBeInTheDocument();
    expect(screen.getByText("HOME$LOADING_REPOSITORIES")).toBeInTheDocument();
  });

  test("shows dropdown when repositories are loaded", async () => {
    // Mock loaded repositories
    (
      useUserRepositories as unknown as ReturnType<typeof vi.fn>
    ).mockReturnValue({
      data: {
        pages: [
          {
            data: [
              { id: "1", full_name: "user/repo1" },
              { id: "2", full_name: "user/repo2" },
            ],
          },
        ],
      },
      isLoading: false,
      isError: false,
    });

    render(<RepositorySelectionForm onRepoSelection={mockOnRepoSelection} />);

    // Check if dropdown is displayed
    expect(screen.getByTestId("repo-dropdown")).toBeInTheDocument();
  });

  test("shows error message when repository fetch fails", async () => {
    // Mock error state
    (
      useUserRepositories as unknown as ReturnType<typeof vi.fn>
    ).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new Error("Failed to fetch repositories"),
    });

    render(<RepositorySelectionForm onRepoSelection={mockOnRepoSelection} />);

    // Check if error message is displayed
    expect(screen.getByTestId("repo-dropdown-error")).toBeInTheDocument();
    expect(
      screen.getByText("HOME$FAILED_TO_LOAD_REPOSITORIES"),
    ).toBeInTheDocument();
  });
});
