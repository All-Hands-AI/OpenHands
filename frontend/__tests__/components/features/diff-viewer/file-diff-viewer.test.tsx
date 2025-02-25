import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { describe, expect, it, vi } from "vitest";
import {
  FileDiffViewer,
  FileDiffViewerProps,
} from "#/components/features/diff-viewer/file-diff-viewer";

describe("FileDiffViewer", () => {
  const original = "before_content";
  const modified = "after_content";

  // Mocking the DiffEditor component because it does not render past the "Loading..." state
  vi.mock("@monaco-editor/react", () => ({
    DiffEditor: ({
      original: mockOriginal,
      modified: mockModified,
    }: Pick<FileDiffViewerProps, "modified" | "original">) => (
      <div data-testid="file-diff-viewer">
        <p>{mockOriginal}</p>
        <p>{mockModified}</p>
      </div>
    ),
  }));

  it("should render the file diff viewer by default", async () => {
    render(
      <FileDiffViewer
        label="some/file/path"
        original={original}
        modified={modified}
      />,
    );

    const wrapper = screen.getByTestId("file-diff-viewer-outer");
    const viewer = await within(wrapper).findByTestId("file-diff-viewer");
    within(viewer).getByText(original);
    within(viewer).getByText(modified);
  });

  it("should render the file path", () => {
    render(
      <FileDiffViewer
        label="some/file/path"
        original={original}
        modified={modified}
      />,
    );

    const wrapper = screen.getByTestId("file-diff-viewer-outer");
    within(wrapper).getByText("some/file/path");
  });

  it("should collapse the file diff", async () => {
    render(
      <FileDiffViewer
        label="some/file/path"
        original={original}
        modified={modified}
      />,
    );

    const button = screen.getByTestId("collapse");
    await userEvent.click(button);

    const wrapper = screen.getByTestId("file-diff-viewer-outer");
    const viewer = within(wrapper).queryByTestId("file-diff-viewer");

    expect(viewer).not.toBeVisible();

    await userEvent.click(button);

    expect(viewer).toBeVisible();
  });

  it.todo("should expand the file diff");
});
