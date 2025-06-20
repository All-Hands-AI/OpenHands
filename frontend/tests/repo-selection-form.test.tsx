import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { RepositorySelectionForm } from "../src/components/features/home/repo-selection-form";
import { useUserRepositories } from "../src/hooks/query/use-user-repositories";
import { useRepositoryBranches } from "../src/hooks/query/use-repository-branches";
import { useCreateConversation } from "../src/hooks/mutation/use-create-conversation";
import { useIsCreatingConversation } from "../src/hooks/use-is-creating-conversation";

// Mock the hooks
vi.mock("../src/hooks/query/use-user-repositories");
vi.mock("../src/hooks/query/use-repository-branches");
vi.mock("../src/hooks/mutation/use-create-conversation");
vi.mock("../src/hooks/use-is-creating-conversation");
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

describe("RepositorySelectionForm", () => {
  const mockOnRepoSelection = vi.fn();

  beforeEach(() => {
    vi.resetAllMocks();

    // Mock the hooks with default values
    (useUserRepositories as any).mockReturnValue({
      data: [
        { id: "1", full_name: "test/repo1" },
        { id: "2", full_name: "test/repo2" }
      ],
      isLoading: false,
      isError: false,
    });

    (useRepositoryBranches as any).mockReturnValue({
      data: [
        { name: "main" },
        { name: "develop" }
      ],
      isLoading: false,
      isError: false,
    });

    (useCreateConversation as any).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isSuccess: false,
    });

    (useIsCreatingConversation as any).mockReturnValue(false);
  });

  it("should clear selected branch when input is empty", async () => {
    render(<RepositorySelectionForm onRepoSelection={mockOnRepoSelection} />);

    // First select a repository to enable the branch dropdown
    const repoDropdown = screen.getByTestId("repository-dropdown");
    fireEvent.change(repoDropdown, { target: { value: "test/repo1" } });

    // Get the branch dropdown and verify it's enabled
    const branchDropdown = screen.getByTestId("branch-dropdown");
    expect(branchDropdown).not.toBeDisabled();

    // Simulate deleting all text in the branch input
    fireEvent.change(branchDropdown, { target: { value: "" } });

    // Verify the branch input is cleared (no selected branch)
    expect(branchDropdown).toHaveValue("");
  });

  it("should clear selected branch when input contains only whitespace", async () => {
    render(<RepositorySelectionForm onRepoSelection={mockOnRepoSelection} />);

    // First select a repository to enable the branch dropdown
    const repoDropdown = screen.getByTestId("repository-dropdown");
    fireEvent.change(repoDropdown, { target: { value: "test/repo1" } });

    // Get the branch dropdown and verify it's enabled
    const branchDropdown = screen.getByTestId("branch-dropdown");
    expect(branchDropdown).not.toBeDisabled();

    // Simulate entering only whitespace in the branch input
    fireEvent.change(branchDropdown, { target: { value: "   " } });

    // Verify the branch input is cleared (no selected branch)
    expect(branchDropdown).toHaveValue("");
  });

  it("should keep branch empty after being cleared even with auto-selection", async () => {
    render(<RepositorySelectionForm onRepoSelection={mockOnRepoSelection} />);

    // First select a repository to enable the branch dropdown
    const repoDropdown = screen.getByTestId("repository-dropdown");
    fireEvent.change(repoDropdown, { target: { value: "test/repo1" } });

    // Get the branch dropdown and verify it's enabled
    const branchDropdown = screen.getByTestId("branch-dropdown");
    expect(branchDropdown).not.toBeDisabled();

    // The branch should be auto-selected to "main" initially
    expect(branchDropdown).toHaveValue("main");

    // Simulate deleting all text in the branch input
    fireEvent.change(branchDropdown, { target: { value: "" } });

    // Verify the branch input is cleared (no selected branch)
    expect(branchDropdown).toHaveValue("");

    // Trigger a re-render by changing something else
    fireEvent.change(repoDropdown, { target: { value: "test/repo2" } });
    fireEvent.change(repoDropdown, { target: { value: "test/repo1" } });

    // The branch should be auto-selected to "main" again after repo change
    expect(branchDropdown).toHaveValue("main");

    // Clear it again
    fireEvent.change(branchDropdown, { target: { value: "" } });

    // Verify it stays empty
    expect(branchDropdown).toHaveValue("");

    // Simulate a component update without changing repos
    // This would normally trigger the useEffect if our fix wasn't working
    fireEvent.blur(branchDropdown);

    // Verify it still stays empty
    expect(branchDropdown).toHaveValue("");
  });
});
