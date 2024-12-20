import { screen } from "@testing-library/react";
import { renderWithProviders } from "test-utils";
import { describe, afterEach, vi, it, expect } from "vitest";
import { ExplorerTree } from "#/components/features/file-explorer/explorer-tree";

const FILES = ["file-1-1.ts", "folder-1-2"];

describe.skip("ExplorerTree", () => {
  afterEach(() => {
    vi.resetAllMocks();
  });

  it("should render the explorer", () => {
    renderWithProviders(<ExplorerTree files={FILES} defaultOpen />);

    expect(screen.getByText("file-1-1.ts")).toBeInTheDocument();
    expect(screen.getByText("folder-1-2")).toBeInTheDocument();
    // TODO: make sure children render
  });

  it("should render the explorer given the defaultExpanded prop", () => {
    renderWithProviders(<ExplorerTree files={FILES} />);

    expect(screen.queryByText("file-1-1.ts")).toBeInTheDocument();
    expect(screen.queryByText("folder-1-2")).toBeInTheDocument();
    // TODO: make sure children don't render
  });
});
