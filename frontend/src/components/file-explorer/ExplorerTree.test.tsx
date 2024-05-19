import React from "react";
import { renderWithProviders } from "test-utils";
import ExplorerTree from "./ExplorerTree";

const FILES = ["file-1-1.ts", "folder-1-2"];

describe("ExplorerTree", () => {
  afterEach(() => {
    vi.resetAllMocks();
  });

  it("should render the explorer", () => {
    const { getByText } = renderWithProviders(
      <ExplorerTree files={FILES} defaultOpen />,
    );

    expect(getByText("file-1-1.ts")).toBeInTheDocument();
    expect(getByText("folder-1-2")).toBeInTheDocument();
    // TODO: make sure children render
  });

  it("should render the explorer given the defaultExpanded prop", () => {
    const { queryByText } = renderWithProviders(<ExplorerTree files={FILES} />);

    expect(queryByText("file-1-1.ts")).toBeInTheDocument();
    expect(queryByText("folder-1-2")).toBeInTheDocument();
    // TODO: make sure children don't render
  });

  it.todo("should render all children as collapsed when defaultOpen is false");

  it.todo(
    "should maintain the expanded state of child folders when closing and opening a parent folder",
  );
});
