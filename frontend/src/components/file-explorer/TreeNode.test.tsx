import React from "react";
import { act, render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import TreeNode from "./TreeNode";
import { selectFile, listFiles } from "#/services/fileService";

vi.mock("../../services/fileService", async () => ({
  listFiles: vi.fn(async (path: string = '/') => {
      if (path === "/") {
          return ["folder1/", "file1.ts"];
      } else if (path === "/folder1/") {
          return ["file2.ts"];
      }
  }),
  selectFile: vi.fn(async (path: string) => {
    return {code: "Hello world!"};
  }),
  uploadFile: vi.fn(),
}));


describe("TreeNode", () => {
  afterEach(() => {
    vi.resetAllMocks();
  });

  it("should render a file if property has no children", () => {
    const { getByText } = render(
      <TreeNode
        path={"/file.ts"}
        defaultOpen
      />,
    );

    expect(getByText("file.ts")).toBeInTheDocument();
  });

  it("should render a folder if it's in a subdir", () => {
    const { getByText } = render(
      <TreeNode
        path={"/folder1/"}
        defaultOpen
      />,
    );

    expect(getByText("folder1")).toBeInTheDocument();
    expect(getByText("file2.ts")).toBeInTheDocument();
  });

  it("should close a folder when clicking on it", () => {
    const { getByText, queryByText } = render(
      <TreeNode
        path={"/folder1/"}
        defaultOpen
      />,
    );

    expect(queryByText("folder1")).toBeInTheDocument();
    expect(getByText("file2.ts")).toBeInTheDocument();

    act(() => {
      userEvent.click(getByText("folder"));
    });

    expect(queryByText("folder1")).toBeInTheDocument();
    expect(getByText("file2.ts")).not.toBeInTheDocument();
  });

  it("should open a folder when clicking on it", () => {
    const { getByText, queryByText } = render(
      <TreeNode path={"/folder1/"} />,
    );

    expect(queryByText("folder1")).toBeInTheDocument();
    expect(getByText("file2.ts")).not.toBeInTheDocument();

    act(() => {
      userEvent.click(getByText("folder"));
    });

    expect(getByText("folder2")).toBeInTheDocument();
    expect(getByText("file.ts")).toBeInTheDocument();
  });

  it("should call a fn and return the full path of a file when clicking on it", () => {
    const { getByText } = render(
      <TreeNode
        path={"/folder/file2.ts"}
        defaultOpen
      />,
    );

    act(() => {
      userEvent.click(getByText("file2.ts"));
    });

    expect(selectFile).toHaveBeenCalledWith("/folder1/file2.ts");
  });

  it("should render the explorer given the defaultExpanded prop", () => {
    const { getByText, queryByText } = render(
      <TreeNode path={"/folder1/"} />,
    );

    expect(getByText("folder1")).toBeInTheDocument();
    expect(queryByText("file2.ts")).not.toBeInTheDocument();
    expect(queryByText("file1.ts")).not.toBeInTheDocument();

    act(() => {
      userEvent.click(getByText("folder1"));
    });

    expect(getByText("file1.ts")).toBeInTheDocument();
  });

  it("should render all children as collapsed when defaultOpen is false", () => {
    const { getByText, queryByText } = render(
      <TreeNode path={"/folder1/"} />,
    );

    expect(getByText("folder1")).toBeInTheDocument();

    act(() => {
      userEvent.click(getByText("folder1"));
    });

    expect(getByText("folder1")).toBeInTheDocument();
    expect(getByText("file1.ts")).toBeInTheDocument();
  });
});
