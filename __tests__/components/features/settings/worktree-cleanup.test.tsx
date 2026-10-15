import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import WorktreesService, {
  type ConversationWorktree,
} from "#/api/worktrees-service";
import { WorktreeCleanup } from "#/components/features/settings/runtime/worktree-cleanup";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";

vi.mock("#/utils/custom-toast-handlers", () => ({
  displayErrorToast: vi.fn(),
  displaySuccessToast: vi.fn(),
}));

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

  it("confirms removing the last worktree although its row is gone", async () => {
    vi.spyOn(WorktreesService, "list")
      .mockResolvedValueOnce([worktree("last")])
      .mockResolvedValue([]);
    vi.spyOn(WorktreesService, "remove").mockResolvedValue();
    renderCleanup();

    await userEvent.click(await screen.findByTestId("remove-worktree-last"));

    await waitFor(() => expect(displaySuccessToast).toHaveBeenCalled());
    expect(screen.queryByTestId("worktree-cleanup")).toBeNull();
  });

  it("shows why the server refused a removal", async () => {
    vi.spyOn(WorktreesService, "list").mockResolvedValue([worktree("raced")]);
    vi.spyOn(WorktreesService, "remove").mockRejectedValue(
      Object.assign(new Error("HTTP 409"), {
        response: { detail: "It has uncommitted or untracked changes" },
      }),
    );
    renderCleanup();

    await userEvent.click(await screen.findByTestId("remove-worktree-raced"));

    await waitFor(() =>
      expect(displayErrorToast).toHaveBeenCalledWith(
        "It has uncommitted or untracked changes",
      ),
    );
  });

  it("shows nothing when there are no worktrees", async () => {
    const list = vi.spyOn(WorktreesService, "list").mockResolvedValue([]);
    renderCleanup();

    await waitFor(() => expect(list).toHaveBeenCalled());
    expect(screen.queryByTestId("worktree-cleanup")).toBeNull();
  });
});
