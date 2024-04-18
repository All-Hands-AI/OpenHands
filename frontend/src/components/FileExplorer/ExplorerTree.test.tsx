import React from "react";
import { act, render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ExplorerTree from "./ExplorerTree";

const onFileClick = vi.fn();

describe("ExplorerTree", () => {
  afterEach(() => {
    vi.resetAllMocks();
  });

  it("should render a file if property has no children", () => {
    const tree: TreeNode[] = [{ name: "file.ts" }];

    const { getByText } = render(
      <ExplorerTree tree={tree} onFileClick={onFileClick} />,
    );
    expect(getByText("file.ts")).toBeInTheDocument();
  });

  it("should render a folder if property has children", () => {
    const tree: TreeNode[] = [
      { name: "folder", children: [{ name: "file.ts" }] },
    ];

    const { getByText } = render(
      <ExplorerTree tree={tree} onFileClick={onFileClick} />,
    );
    expect(getByText("folder")).toBeInTheDocument();
    expect(getByText("file.ts")).toBeInTheDocument();
  });

  it("should close a folder when clicking on it", () => {
    const tree: TreeNode[] = [
      {
        name: "folder",
        children: [
          { name: "folder2", children: [{ name: "file2.ts" }] },
          { name: "file.ts" },
        ],
      },
    ];

    const { getByText, queryByText } = render(
      <ExplorerTree tree={tree} onFileClick={onFileClick} />,
    );

    act(() => {
      userEvent.click(getByText("folder2"));
    });

    expect(queryByText("file2.ts")).not.toBeInTheDocument();
    expect(getByText("folder")).toBeInTheDocument();
    expect(getByText("file.ts")).toBeInTheDocument();
  });

  it("should open a folder when clicking on it", () => {
    const tree: TreeNode[] = [
      {
        name: "folder",
        children: [
          { name: "folder2", children: [{ name: "file2.ts" }] },
          { name: "file.ts" },
        ],
      },
    ];

    const { getByText, queryByText } = render(
      <ExplorerTree tree={tree} onFileClick={onFileClick} />,
    );

    act(() => {
      userEvent.click(getByText("folder"));
    });

    expect(queryByText("folder2")).not.toBeInTheDocument();
    expect(queryByText("file2.ts")).not.toBeInTheDocument();
    expect(queryByText("file.ts")).not.toBeInTheDocument();

    act(() => {
      userEvent.click(getByText("folder"));
    });

    expect(getByText("folder2")).toBeInTheDocument();
    expect(getByText("file2.ts")).toBeInTheDocument();
    expect(getByText("file.ts")).toBeInTheDocument();
  });

  it("should return the full path of a file when clicking on it", () => {
    const tree: TreeNode[] = [
      {
        name: "folder",
        children: [
          { name: "folder2", children: [{ name: "file2.ts" }] },
          { name: "file.ts" },
        ],
      },
    ];

    const { getByText } = render(
      <ExplorerTree tree={tree} onFileClick={onFileClick} />,
    );

    act(() => {
      userEvent.click(getByText("file.ts"));
    });

    expect(onFileClick).toHaveBeenCalledWith("folder/file.ts");

    act(() => {
      userEvent.click(getByText("file2.ts"));
    });

    expect(onFileClick).toHaveBeenCalledWith("folder/folder2/file2.ts");
  });

  it.todo("should be able to render all contents expanded or collapsed");

  it.todo(
    "should maintain the expanded state of child folders when closing and opening a parent folder",
  );
});
