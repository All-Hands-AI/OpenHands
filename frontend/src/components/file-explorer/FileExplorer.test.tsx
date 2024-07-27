import React from "react";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "test-utils";
import { describe, it, expect, vi, Mock } from "vitest";
import FileExplorer from "./FileExplorer";
import { uploadFiles, listFiles } from "#/services/fileService";
import toast from "#/utils/toast";
import AgentState from "#/types/AgentState";

const toastSpy = vi.spyOn(toast, "error");

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

  uploadFiles: vi.fn(),
}));

const renderFileExplorerWithRunningAgentState = () =>
  renderWithProviders(<FileExplorer />, {
    preloadedState: {
      agent: {
        curAgentState: AgentState.RUNNING,
      },
    },
  });

describe("FileExplorer", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should get the workspace directory", async () => {
    renderFileExplorerWithRunningAgentState();

    expect(await screen.findByText("folder1")).toBeInTheDocument();
    expect(await screen.findByText("file1.ts")).toBeInTheDocument();
    expect(listFiles).toHaveBeenCalledTimes(1); // once for root
  });

  it.todo("should render an empty workspace");

  it("should refetch the workspace when clicking the refresh button", async () => {
    const user = userEvent.setup();
    renderFileExplorerWithRunningAgentState();

    expect(await screen.findByText("folder1")).toBeInTheDocument();
    expect(await screen.findByText("file1.ts")).toBeInTheDocument();
    expect(listFiles).toHaveBeenCalledTimes(1); // once for root

    const refreshButton = screen.getByTestId("refresh");
    await user.click(refreshButton);

    expect(listFiles).toHaveBeenCalledTimes(2); // once for root, once for refresh button
  });

  it("should toggle the explorer visibility when clicking the toggle button", async () => {
    const user = userEvent.setup();
    renderFileExplorerWithRunningAgentState();

    const folder1 = await screen.findByText("folder1");
    expect(folder1).toBeInTheDocument();

    const toggleButton = screen.getByTestId("toggle");
    await user.click(toggleButton);

    expect(folder1).toBeInTheDocument();
    expect(folder1).not.toBeVisible();
  });

  it("should upload files", async () => {
    const user = userEvent.setup();
    renderFileExplorerWithRunningAgentState();

    const file = new File([""], "file-name");
    const uploadFileInput = await screen.findByTestId("file-input");
    await user.upload(uploadFileInput, file);

    // TODO: Improve this test by passing expected argument to `uploadFiles`
    expect(uploadFiles).toHaveBeenCalledOnce();
    expect(listFiles).toHaveBeenCalled();

    const file2 = new File([""], "file-name-2");
    const uploadDirInput = await screen.findByTestId("file-input");
    await user.upload(uploadDirInput, [file, file2]);

    expect(uploadFiles).toHaveBeenCalledTimes(2);
    expect(listFiles).toHaveBeenCalled();
  });

  it.todo("should upload files when dragging them to the explorer", () => {
    // It will require too much work to mock drag logic, especially for our case
    // https://github.com/testing-library/user-event/issues/440#issuecomment-685010755
    // TODO: should be tested in an e2e environment such as Cypress/Playwright
  });

  it.todo("should download a file");

  it("should display an error toast if file upload fails", async () => {
    (uploadFiles as Mock).mockRejectedValue(new Error());
    const user = userEvent.setup();
    renderFileExplorerWithRunningAgentState();

    const uploadFileInput = await screen.findByTestId("file-input");
    const file = new File([""], "test");

    await user.upload(uploadFileInput, file);

    expect(uploadFiles).rejects.toThrow();
    expect(toastSpy).toHaveBeenCalledWith(
      expect.stringContaining("upload-error"),
      expect.any(String),
    );
  });
});
