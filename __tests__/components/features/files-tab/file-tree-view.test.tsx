import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, afterEach } from "vitest";
import { FileTreeView } from "#/components/features/files-tab/file-tree-view";
import { WorkspacePath } from "#/components/features/files-tab/workspace-path";

// FileTreeView composes the recursive TreeNode (extracted into its own file).
// The route-level files-tab test treats the tree as a black box, so these
// cover the tree's own user-facing behavior: empty state, directory
// expand/collapse, and file selection.
describe("FileTreeView", () => {
  it("shows the empty-state message and no tree when there are no files", () => {
    // Arrange + Act
    render(
      <FileTreeView paths={[]} selectedPath={null} onSelectFile={vi.fn()} />,
    );

    // Assert
    expect(screen.getByText("FILES$NO_FILES")).toBeInTheDocument();
    expect(screen.queryByTestId("file-tree-view")).not.toBeInTheDocument();
  });

  it("keeps a directory collapsed until clicked, then reveals its children", async () => {
    // Arrange
    const user = userEvent.setup();
    render(
      <FileTreeView
        paths={["src/main.ts"]}
        selectedPath={null}
        onSelectFile={vi.fn()}
      />,
    );

    // Assert: the directory row shows but its nested file is hidden.
    expect(screen.getByTestId("file-tree-dir-src")).toBeInTheDocument();
    expect(
      screen.queryByTestId("file-tree-file-src/main.ts"),
    ).not.toBeInTheDocument();

    // Act: expand the directory.
    await user.click(screen.getByTestId("file-tree-dir-src"));

    // Assert: the nested file is now visible.
    expect(
      screen.getByTestId("file-tree-file-src/main.ts"),
    ).toBeInTheDocument();
  });

  it("calls onSelectFile with the file path when a file row is clicked", async () => {
    // Arrange
    const user = userEvent.setup();
    const onSelectFile = vi.fn();
    render(
      <FileTreeView
        paths={["README.md"]}
        selectedPath={null}
        onSelectFile={onSelectFile}
      />,
    );

    // Act
    await user.click(screen.getByTestId("file-tree-file-README.md"));

    // Assert
    expect(onSelectFile).toHaveBeenCalledTimes(1);
    expect(onSelectFile).toHaveBeenCalledWith("README.md");
  });
});

describe("workspace-path", () => {
  const originalClipboard = navigator.clipboard;

  describe("WorkspacePath", () => {
    afterEach(() => {
      vi.restoreAllMocks();
      Object.defineProperty(navigator, "clipboard", {
        configurable: true,
        value: originalClipboard,
      });
    });

    it("shows the effective workspace path", () => {
      const path = "/Users/alice/workspace/project/abc123";

      render(<WorkspacePath path={path} />);

      expect(screen.getByTestId("files-tab-workspace-path")).toHaveTextContent(
        "WORKSPACE$TITLE:",
      );
      expect(
        screen.getByTestId("files-tab-workspace-path-value"),
      ).toHaveTextContent(path);
    });

    it("keeps the complete path available when the text is truncated", () => {
      const path =
        "/Users/alice/a-very-long-workspace-name/project/with/nested/directories";

      render(<WorkspacePath path={path} />);

      const value = screen.getByTestId("files-tab-workspace-path-value");
      expect(value).toHaveClass("truncate");
      expect(value).toHaveAttribute("title", path);
    });

    it("copies the complete path and confirms the action", async () => {
      const path = "C:\\Users\\alice\\workspace\\project";
      const writeText = vi.fn().mockResolvedValue(undefined);
      const user = userEvent.setup();
      Object.defineProperty(navigator, "clipboard", {
        configurable: true,
        value: { writeText },
      });

      render(<WorkspacePath path={path} />);

      const workspacePath = screen.getByTestId("files-tab-workspace-path");
      await user.click(
        within(workspacePath).getByRole("button", { name: "BUTTON$COPY" }),
      );

      expect(writeText).toHaveBeenCalledWith(path);
      expect(
        within(workspacePath).getByRole("button", { name: "BUTTON$COPIED" }),
      ).toBeDisabled();
    });

    it("does not render without a workspace path", () => {
      const { rerender } = render(<WorkspacePath path={null} />);

      expect(
        screen.queryByTestId("files-tab-workspace-path"),
      ).not.toBeInTheDocument();

      rerender(<WorkspacePath path="   " />);
      expect(
        screen.queryByTestId("files-tab-workspace-path"),
      ).not.toBeInTheDocument();
    });
  });
});
