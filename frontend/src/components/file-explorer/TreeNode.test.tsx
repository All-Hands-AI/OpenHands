import React from "react";
import { waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "test-utils";
import TreeNode from "./TreeNode";
import { selectFile, listFiles } from "#/services/fileService";

vi.mock("../../services/fileService", async () => ({
  listFiles: vi.fn(async (path: string = "/") => {
    if (path === "/") {
      return Promise.resolve(["folder1/", "file1.ts"]);
    }
    if (path === "/folder1/" || path === "folder1/") {
      return Promise.resolve(["file2.ts"]);
    }
    return Promise.resolve([]);
  }),
  selectFile: vi.fn(async () => Promise.resolve({ code: "Hello world!" })),
  uploadFile: vi.fn(),
}));

describe("TreeNode", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render a file if property has no children", () => {
    const { getByText } = renderWithProviders(
      <TreeNode path="/file.ts" defaultOpen />,
    );

    expect(getByText("file.ts")).toBeInTheDocument();
  });

  it("should render a folder if it's in a subdir", async () => {
    const { findByText } = renderWithProviders(
      <TreeNode path="/folder1/" defaultOpen />,
    );
    expect(listFiles).toHaveBeenCalledWith("/folder1/");

    expect(await findByText("folder1")).toBeInTheDocument();
    expect(await findByText("file2.ts")).toBeInTheDocument();
  });

  it("should close a folder when clicking on it", async () => {
    const { findByText, queryByText } = renderWithProviders(
      <TreeNode path="/folder1/" defaultOpen />,
    );

    expect(await findByText("folder1")).toBeInTheDocument();
    expect(await findByText("file2.ts")).toBeInTheDocument();

    act(async () => {
      userEvent.click(await findByText("folder1"));
    });

    expect(await findByText("folder1")).toBeInTheDocument();
    expect(await queryByText("file2.ts")).not.toBeInTheDocument();
  });

  it("should open a folder when clicking on it", async () => {
    const { getByText, findByText, queryByText } = renderWithProviders(
      <TreeNode path="/folder1/" />,
    );

    expect(await findByText("folder1")).toBeInTheDocument();
    expect(await queryByText("file2.ts")).not.toBeInTheDocument();

    act(() => {
      userEvent.click(getByText("folder1"));
    });
    expect(listFiles).toHaveBeenCalledWith("/folder1/");

    expect(await findByText("folder1")).toBeInTheDocument();
    expect(await findByText("file2.ts")).toBeInTheDocument();
  });

  it.only("should call a fn and return the full path of a file when clicking on it", () => {
    const { getByText } = renderWithProviders(
      <TreeNode path="/folder1/file2.ts" defaultOpen />,
    );

    act(() => {
      userEvent.click(getByText("file2.ts"));
    });

    waitFor(() => {
      expect(selectFile).toHaveBeenCalledWith("/folder1/file2.ts");
    });
  });

  it("should render the explorer given the defaultOpen prop", async () => {
    const { getByText, findByText, queryByText } = renderWithProviders(
      <TreeNode path="/" defaultOpen />,
    );

    expect(listFiles).toHaveBeenCalledWith("/");

    expect(await findByText("file1.ts")).toBeInTheDocument();
    expect(await findByText("folder1")).toBeInTheDocument();
    expect(await queryByText("file2.ts")).not.toBeInTheDocument();

    act(() => {
      userEvent.click(getByText("folder1"));
    });

    expect(listFiles).toHaveBeenCalledWith("folder1/");

    expect(await findByText("file1.ts")).toBeInTheDocument();
    expect(await findByText("folder1")).toBeInTheDocument();
    expect(await findByText("file2.ts")).toBeInTheDocument();
  });

  it("should render all children as collapsed when defaultOpen is false", async () => {
    const { findByText, getByText, queryByText } = renderWithProviders(
      <TreeNode path="/folder1/" />,
    );

    expect(await findByText("folder1")).toBeInTheDocument();
    expect(await queryByText("file2.ts")).not.toBeInTheDocument();

    act(() => {
      userEvent.click(getByText("folder1"));
    });
    expect(listFiles).toHaveBeenCalledWith("/folder1/");

    expect(await findByText("folder1")).toBeInTheDocument();
    expect(await findByText("file2.ts")).toBeInTheDocument();
  });
});
