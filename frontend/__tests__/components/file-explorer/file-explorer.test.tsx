import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "test-utils";
import { describe, it, expect, vi, Mock, afterEach } from "vitest";
import toast from "#/utils/toast";
import { AgentState } from "#/types/agent-state";
import OpenHands from "#/api/open-hands";
import { FileExplorer } from "#/components/features/file-explorer/file-explorer";

const toastSpy = vi.spyOn(toast, "error");
const uploadFilesSpy = vi.spyOn(OpenHands, "uploadFiles");
const getFilesSpy = vi.spyOn(OpenHands, "getFiles");

vi.mock("../../services/fileService", async () => ({
  uploadFiles: vi.fn(),
}));

const renderFileExplorerWithRunningAgentState = () =>
  renderWithProviders(<FileExplorer isOpen onToggle={() => {}} />, {
    preloadedState: {
      agent: {
        curAgentState: AgentState.RUNNING,
      },
    },
  });

describe.skip("FileExplorer", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should get the workspace directory", async () => {
    renderFileExplorerWithRunningAgentState();

    expect(await screen.findByText("folder1")).toBeInTheDocument();
    expect(await screen.findByText("file1.ts")).toBeInTheDocument();
    expect(getFilesSpy).toHaveBeenCalledTimes(1); // once for root
  });

  it("should refetch the workspace when clicking the refresh button", async () => {
    const user = userEvent.setup();
    renderFileExplorerWithRunningAgentState();

    expect(await screen.findByText("folder1")).toBeInTheDocument();
    expect(await screen.findByText("file1.ts")).toBeInTheDocument();
    expect(getFilesSpy).toHaveBeenCalledTimes(1); // once for root

    const refreshButton = screen.getByTestId("refresh");
    await user.click(refreshButton);

    expect(getFilesSpy).toHaveBeenCalledTimes(2); // once for root, once for refresh button
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
    expect(uploadFilesSpy).toHaveBeenCalledOnce();
    expect(getFilesSpy).toHaveBeenCalled();

    const file2 = new File([""], "file-name-2");
    const uploadDirInput = await screen.findByTestId("file-input");
    await user.upload(uploadDirInput, [file, file2]);

    expect(uploadFilesSpy).toHaveBeenCalledTimes(2);
    expect(getFilesSpy).toHaveBeenCalled();
  });

  it("should display an error toast if file upload fails", async () => {
    (uploadFilesSpy as Mock).mockRejectedValue(new Error());
    const user = userEvent.setup();
    renderFileExplorerWithRunningAgentState();

    const uploadFileInput = await screen.findByTestId("file-input");
    const file = new File([""], "test");

    await user.upload(uploadFileInput, file);

    expect(uploadFilesSpy).rejects.toThrow();
    expect(toastSpy).toHaveBeenCalledWith(
      expect.stringContaining("upload-error"),
      expect.any(String),
    );
  });
});
