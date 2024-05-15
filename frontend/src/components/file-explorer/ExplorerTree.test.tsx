import React from "react";
import { render } from "@testing-library/react";
import ExplorerTree from "./ExplorerTree";

const FILES = ["file-1-1.ts", "folder-1-2"];

describe("ExplorerTree", () => {
  afterEach(() => {
    vi.resetAllMocks();
  });

  it("should render the explorer", () => {
    const { getByText, queryByText } = render(
      <ExplorerTree files={FILES} defaultOpen />,
    );

    expect(getByText("root-folder-1")).toBeInTheDocument();
    expect(getByText("file-1-1.ts")).toBeInTheDocument();
    expect(getByText("folder-1-2")).toBeInTheDocument();
    expect(queryByText("file-1-2.ts")).not.toBeInTheDocument();
  });

  it("should render the explorer given the defaultExpanded prop", () => {
    const { getByText, queryByText } = render(
      <ExplorerTree files={FILES} />,
    );

    expect(getByText("root-folder-1")).toBeInTheDocument();
    expect(queryByText("file-1-1.ts")).not.toBeInTheDocument();
    expect(queryByText("folder-1-2")).not.toBeInTheDocument();
    expect(queryByText("file-1-2.ts")).not.toBeInTheDocument();
  });

  it.todo("should render all children as collapsed when defaultOpen is false");

  it.todo(
    "should maintain the expanded state of child folders when closing and opening a parent folder",
  );
});
