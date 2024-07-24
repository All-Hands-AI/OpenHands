import React from "react";
import { screen } from "@testing-library/react";
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
    renderWithProviders(<TreeNode path="/file.ts" defaultOpen />);
    expect(screen.getByText("file.ts")).toBeInTheDocument();
  });

  it("should render a folder if it's in a subdir", async () => {
    renderWithProviders(<TreeNode path="/folder1/" defaultOpen />);
    expect(listFiles).toHaveBeenCalledWith("/folder1/");

    expect(await screen.findByText("folder1")).toBeInTheDocument();
    expect(await screen.findByText("file2.ts")).toBeInTheDocument();
  });

  it("should close a folder when clicking on it", async () => {
    const user = userEvent.setup();
    renderWithProviders(<TreeNode path="/folder1/" defaultOpen />);

    const folder1 = await screen.findByText("folder1");
    const file2 = await screen.findByText("file2.ts");

    expect(folder1).toBeInTheDocument();
    expect(file2).toBeInTheDocument();

    await user.click(folder1);

    expect(folder1).toBeInTheDocument();
    expect(screen.queryByText("file2.ts")).not.toBeInTheDocument();
  });

  it("should open a folder when clicking on it", async () => {
    const user = userEvent.setup();
    renderWithProviders(<TreeNode path="/folder1/" />);

    const folder1 = await screen.findByText("folder1");

    expect(folder1).toBeInTheDocument();
    expect(screen.queryByText("file2.ts")).not.toBeInTheDocument();

    await user.click(folder1);
    expect(listFiles).toHaveBeenCalledWith("/folder1/");

    expect(folder1).toBeInTheDocument();
    expect(await screen.findByText("file2.ts")).toBeInTheDocument();
  });

  it("should call `selectFile` and return the full path of a file when clicking on a file", async () => {
    const user = userEvent.setup();
    renderWithProviders(<TreeNode path="/folder1/file2.ts" defaultOpen />);

    const file2 = screen.getByText("file2.ts");
    await user.click(file2);

    expect(selectFile).toHaveBeenCalledWith("/folder1/file2.ts");
  });

  it("should render the full explorer given the defaultOpen prop", async () => {
    const user = userEvent.setup();
    renderWithProviders(<TreeNode path="/" defaultOpen />);

    expect(listFiles).toHaveBeenCalledWith("/");

    const file1 = await screen.findByText("file1.ts");
    const folder1 = await screen.findByText("folder1");

    expect(file1).toBeInTheDocument();
    expect(folder1).toBeInTheDocument();
    expect(screen.queryByText("file2.ts")).not.toBeInTheDocument();

    await user.click(folder1);
    expect(listFiles).toHaveBeenCalledWith("folder1/");

    expect(file1).toBeInTheDocument();
    expect(folder1).toBeInTheDocument();
    expect(await screen.findByText("file2.ts")).toBeInTheDocument();
  });

  it("should render all children as collapsed when defaultOpen is false", async () => {
    renderWithProviders(<TreeNode path="/folder1/" defaultOpen={false} />);

    const folder1 = await screen.findByText("folder1");

    expect(folder1).toBeInTheDocument();
    expect(screen.queryByText("file2.ts")).not.toBeInTheDocument();

    await userEvent.click(folder1);
    expect(listFiles).toHaveBeenCalledWith("/folder1/");

    expect(folder1).toBeInTheDocument();
    expect(await screen.findByText("file2.ts")).toBeInTheDocument();
  });
});
