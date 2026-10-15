import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import WorktreesService, {
  type ConversationWorktree,
} from "#/api/worktrees-service";
import { WorktreeCleanup } from "#/components/features/settings/runtime/worktree-cleanup";

function worktree(
  name: string,
  overrides: Partial<ConversationWorktree> = {},
): ConversationWorktree {
  return {
    name,
    path: `/tmp/conversation-worktrees/${name}/repo`,
    repository: "/home/me/repo",
    branch: `openhands/${name}`,
    conversation_ids: [name],
    last_activity: null,
    size_bytes: 5 * 1024 ** 2,
    has_changes: false,
    in_use: false,
    ...overrides,
  };
}

function renderCleanup() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(<WorktreeCleanup />, {
    wrapper: ({ children }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    ),
  });
}

describe("WorktreeCleanup", () => {
  it("offers removal only for clean worktrees no open conversation uses", async () => {
    vi.spyOn(WorktreesService, "list").mockResolvedValue([
      worktree("clean"),
      worktree("dirty", { has_changes: true }),
      worktree("open", { in_use: true }),
    ]);
    const remove = vi.spyOn(WorktreesService, "remove").mockResolvedValue();
    renderCleanup();

    await screen.findByTestId("worktree-cleanup");
    expect(screen.queryByTestId("remove-worktree-dirty")).toBeNull();
    expect(screen.queryByTestId("remove-worktree-open")).toBeNull();
    await userEvent.click(screen.getByTestId("remove-worktree-clean"));

    await waitFor(() => expect(remove).toHaveBeenCalledWith("clean"));
  });

  it("shows nothing when there are no worktrees", async () => {
    const list = vi.spyOn(WorktreesService, "list").mockResolvedValue([]);
    renderCleanup();

    await waitFor(() => expect(list).toHaveBeenCalled());
    expect(screen.queryByTestId("worktree-cleanup")).toBeNull();
  });
});
