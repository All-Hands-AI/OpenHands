import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "test-utils";
import { describe, it, expect, vi, afterEach } from "vitest";
import { AgentState } from "#/types/agent-state";
import { FileExplorer } from "#/components/features/file-explorer/file-explorer";
import { FileService } from "#/api/file-service/file-service.api";

const getFilesSpy = vi.spyOn(FileService, "getFiles");

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
});
