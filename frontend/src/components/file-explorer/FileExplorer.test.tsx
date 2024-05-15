import React from "react";
import { waitFor, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { act } from "react-dom/test-utils";
import { renderWithProviders } from "test-utils";
import { describe, it, expect, vi, Mock } from "vitest";
import FileExplorer from "./FileExplorer";
import { uploadFile, listFiles } from "#/services/fileService";
import toast from "#/utils/toast";

const toastSpy = vi.spyOn(toast, "stickyError");

vi.mock("../../services/fileService", async () => ({
  listFiles: vi.fn(async (path: string = '/') => {
      if (path === "/") {
          return Promise.resolve(["folder1/", "file1.ts"]);
      } else if (path === "/folder1/") {
          return Promise.resolve(["file2.ts"]);
      }
  }),

  uploadFile: vi.fn(),
}));

describe("FileExplorer", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it.skip("should get the workspace directory", async () => {
    const { getByText } = renderWithProviders(<FileExplorer />);

    expect(listFiles).toHaveBeenCalledTimes(1);
    await waitFor(() => {
      expect(getByText("root")).toBeInTheDocument();
    });
  });

  it.todo("should render an empty workspace");

  it.skip("should refetch the workspace when clicking the refresh button", async () => {
    renderWithProviders(<FileExplorer />);

    // The 'await' keyword is required here to avoid a warning during test runs
    await act(() => {
      userEvent.click(screen.getByTestId("refresh"));
    });

    expect(listFiles).toHaveBeenCalledTimes(2); // 1 from initial render, 1 from refresh button
  });

  it.skip("should toggle the explorer visibility when clicking the close button", async () => {
    const { getByTestId, getByText, queryByText } = renderWithProviders(
      <FileExplorer />,
    );

    await waitFor(() => {
      expect(getByText("root")).toBeInTheDocument();
    });

    act(() => {
      userEvent.click(getByTestId("toggle"));
    });

    // it should be hidden rather than removed from the DOM
    expect(queryByText("root")).toBeInTheDocument();
    expect(queryByText("root")).not.toBeVisible();
  });

  it("should upload a file", async () => {
    const { getByTestId } = renderWithProviders(<FileExplorer />);

    const uploadFileInput = getByTestId("file-input");
    const file = new File([""], "test");

    // The 'await' keyword is required here to avoid a warning during test runs
    await act(() => {
      userEvent.upload(uploadFileInput, file);
    });

    expect(uploadFile).toHaveBeenCalledWith(file);
    expect(listFiles).toHaveBeenCalled();
  });

  it.todo("should display an error toast if file upload fails", async () => {
    (uploadFile as Mock).mockRejectedValue(new Error());

    const { getByTestId } = renderWithProviders(<FileExplorer />);

    const uploadFileInput = getByTestId("file-input");
    const file = new File([""], "test");

    act(() => {
      userEvent.upload(uploadFileInput, file);
    });

    expect(uploadFile).rejects.toThrow();
    // TODO: figure out why spy isnt called to pass test
    expect(toastSpy).toHaveBeenCalledWith("ws", "Error uploading file");
  });
});
