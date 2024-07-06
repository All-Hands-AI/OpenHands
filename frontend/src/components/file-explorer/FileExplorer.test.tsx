import React from "react";
import { waitFor, act } from "@testing-library/react";
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

describe("FileExplorer", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should get the workspace directory", async () => {
    const { getByText } = renderWithProviders(<FileExplorer />, {
      preloadedState: {
        agent: {
          curAgentState: AgentState.RUNNING,
        },
      },
    });

    await waitFor(() => {
      expect(getByText("folder1")).toBeInTheDocument();
      expect(getByText("file1.ts")).toBeInTheDocument();
    });
    expect(listFiles).toHaveBeenCalledTimes(1); // once for root
  });

  it.todo("should render an empty workspace");

  it("should refetch the workspace when clicking the refresh button", async () => {
    const { getByText, getByTestId } = renderWithProviders(<FileExplorer />, {
      preloadedState: {
        agent: {
          curAgentState: AgentState.RUNNING,
        },
      },
    });
    await waitFor(() => {
      expect(getByText("folder1")).toBeInTheDocument();
      expect(getByText("file1.ts")).toBeInTheDocument();
    });
    expect(listFiles).toHaveBeenCalledTimes(1); // once for root

    await act(async () => {
      await userEvent.click(getByTestId("refresh"));
    });

    await waitFor(() => {
      expect(listFiles).toHaveBeenCalledTimes(2); // once for root, once for refresh button
    });
  });

  it("should toggle the explorer visibility when clicking the close button", async () => {
    const { getByTestId, getByText, queryByText } = renderWithProviders(
      <FileExplorer />,
      {
        preloadedState: {
          agent: {
            curAgentState: AgentState.RUNNING,
          },
        },
      },
    );

    await waitFor(() => {
      expect(getByText("folder1")).toBeInTheDocument();
    });

    await act(async () => {
      await userEvent.click(getByTestId("toggle"));
    });

    expect(queryByText("folder1")).toBeInTheDocument();
    expect(queryByText("folder1")).not.toBeVisible();
  });

  it("should upload files", async () => {
    // TODO: Improve this test by passing expected argument to `uploadFiles`
    const { findByTestId } = renderWithProviders(<FileExplorer />, {
      preloadedState: {
        agent: {
          curAgentState: AgentState.RUNNING,
        },
      },
    });

    const file = new File([""], "file-name");
    const file2 = new File([""], "file-name-2");

    const uploadFileInput = await findByTestId("file-input");

    await act(async () => {
      await userEvent.upload(uploadFileInput, file);
    });

    expect(uploadFiles).toHaveBeenCalledOnce();
    expect(listFiles).toHaveBeenCalled();

    const uploadDirInput = await findByTestId("file-input");

    // The 'await' keyword is required here to avoid a warning during test runs
    await act(async () => {
      await userEvent.upload(uploadDirInput, [file, file2]);
    });

    await waitFor(() => {
      expect(uploadFiles).toHaveBeenCalledTimes(2);
      expect(listFiles).toHaveBeenCalled();
    });
  });

  it.skip("should upload files when dragging them to the explorer", () => {
    // It will require too much work to mock drag logic, especially for our case
    // https://github.com/testing-library/user-event/issues/440#issuecomment-685010755
    // TODO: should be tested in an e2e environment such as Cypress/Playwright
  });

  it.todo("should download a file");

  it.todo("should display an error toast if file upload fails", async () => {
    (uploadFiles as Mock).mockRejectedValue(new Error());

    const { getByTestId } = renderWithProviders(<FileExplorer />);

    const uploadFileInput = getByTestId("file-input");
    const file = new File([""], "test");

    await act(async () => {
      await userEvent.upload(uploadFileInput, file);
    });

    expect(uploadFiles).rejects.toThrow();
    // TODO: figure out why spy isn't called to pass test
    expect(toastSpy).toHaveBeenCalledWith("ws", "Error uploading file");
  });
});
