import React from "react";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "test-utils";
import CodeEditor from "./CodeEditor";

describe("CodeEditor", () => {
  afterEach(() => {
    vi.resetAllMocks();
  });

  it("should render the code editor with save buttons when there is unsaved content", async () => {
    renderWithProviders(<CodeEditor />, {
      preloadedState: {
        code: {
          code: "Content for file1.txt",
          path: "file1.txt", // appears in title
          fileStates: [
            {
              path: "file1.txt",
              unsavedContent: "Updated content for file1.txt",
              savedContent: "Content for file1.txt",
            },
          ],
          refreshID: 1234,
        },
      },
    });

    expect(await screen.findByText("file1.txt")).toBeInTheDocument();
    expect(
      await screen.findByText("CODE_EDITOR$SAVE_LABEL"),
    ).toBeInTheDocument();
  });

  it("should render the code editor without save buttons when there is no unsaved content", async () => {
    renderWithProviders(<CodeEditor />, {
      preloadedState: {
        code: {
          code: "Content for file1.txt",
          path: "file1.txt", // appears in title
          fileStates: [
            {
              path: "file1.txt",
              unsavedContent: "Content for file1.txt",
              savedContent: "Content for file1.txt",
            },
          ],
          refreshID: 1234,
        },
      },
    });

    expect(await screen.findByText("file1.txt")).toBeInTheDocument();
    expect(
      await screen.queryByText("CODE_EDITOR$SAVE_LABEL"),
    ).not.toBeInTheDocument();
  });
});
