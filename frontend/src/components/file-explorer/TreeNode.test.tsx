import React from "react";
import { act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "test-utils";
import TreeNode from "./TreeNode";
import { selectFile, listFiles } from "#/services/fileService";

vi.mock("../../services/fileService", async () => ({
  listFiles: vi.fn(async (path: string = "/") => {
    if (path === "/") {
      return Promise.resolve(["folder1/", "file1.ts"]);
    }
    if (path === "/folder1/") {
      return Promise.resolve(["file2.ts"]);
    }
    return Promise.resolve([]);
  }),
  selectFile: vi.fn(async () => Promise.resolve({ code: "Hello world!" })),
  uploadFile: vi.fn(),
}));

describe("TreeNode", () => {
  afterEach(() => {
    vi.resetAllMocks();
  });

  it("should render a file if property has no children", () => {
    const { getByText } = renderWithProviders(
      <TreeNode path="/file.ts" defaultOpen />,
    );

    expect(getByText("file.ts")).toBeInTheDocument();
  });

  it.skip("should render a folder if it's in a subdir", () => {
    const { getByText } = renderWithProviders(
      <TreeNode path="/folder1/" defaultOpen />,
    );

    expect(getByText("folder1")).toBeInTheDocument();
    expect(getByText("file2.ts")).toBeInTheDocument();
  });

  it.skip("should close a folder when clicking on it", () => {
    const { getByText, queryByText } = renderWithProviders(
      <TreeNode path="/folder1/" defaultOpen />,
    );

    expect(queryByText("folder1")).toBeInTheDocument();
    expect(getByText("file2.ts")).toBeInTheDocument();

    act(() => {
      userEvent.click(getByText("folder"));
    });

    expect(queryByText("folder1")).toBeInTheDocument();
    expect(queryByText("file2.ts")).not.toBeInTheDocument();
  });

  it.skip("should open a folder when clicking on it", () => {
    const { getByText, queryByText } = renderWithProviders(
      <TreeNode path="/folder1/" />,
    );

    expect(queryByText("folder1")).toBeInTheDocument();
    expect(queryByText("file2.ts")).not.toBeInTheDocument();

    act(() => {
      userEvent.click(getByText("folder1"));
    });

    expect(getByText("folder1")).toBeInTheDocument();
    expect(getByText("file2.ts")).toBeInTheDocument();
  });

  it.skip("should call a fn and return the full path of a file when clicking on it", () => {
    const { getByText } = renderWithProviders(
      <TreeNode path="/folder1/file2.ts" defaultOpen />,
    );

    act(() => {
      userEvent.click(getByText("file2.ts"));
    });

    expect(selectFile).toHaveBeenCalledWith("/folder1/file2.ts");
  });

  it.skip("should render the explorer given the defaultExpanded prop", () => {
    const { getByText, queryByText } = renderWithProviders(
      <TreeNode path="/folder1/" />,
    );

    expect(getByText("folder1")).toBeInTheDocument();
    expect(queryByText("file2.ts")).not.toBeInTheDocument();
    expect(queryByText("file1.ts")).not.toBeInTheDocument();

    act(() => {
      userEvent.click(getByText("folder1"));
    });

    expect(getByText("file1.ts")).toBeInTheDocument();
  });

  it.skip("should render all children as collapsed when defaultOpen is false", () => {
    const { getByText, queryByText } = renderWithProviders(
      <TreeNode path="/folder1/" />,
    );

    expect(getByText("folder1")).toBeInTheDocument();
    expect(queryByText("file1.ts")).not.toBeInTheDocument();

    act(() => {
      userEvent.click(getByText("folder1"));
    });
    expect(listFiles).toHaveBeenCalledWith("/folder1/");

    expect(getByText("folder1")).toBeInTheDocument();
    expect(getByText("file1.ts")).toBeInTheDocument();
  });
});
