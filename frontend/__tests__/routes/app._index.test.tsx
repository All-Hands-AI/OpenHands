import { createRemixStub } from "@remix-run/testing";
import { describe, expect, it } from "vitest";
import { screen, within } from "@testing-library/react";
import { renderWithProviders } from "test-utils";
import userEvent from "@testing-library/user-event";
import CodeEditor from "#/routes/app._index/route";

const RemixStub = createRemixStub([{ path: "/app", Component: CodeEditor }]);

describe.skip("CodeEditor", () => {
  it("should render", async () => {
    renderWithProviders(<RemixStub initialEntries={["/app"]} />);
    await screen.findByTestId("file-explorer");
    expect(screen.getByTestId("code-editor-empty-message")).toBeInTheDocument();
  });

  it("should retrieve the files", async () => {
    renderWithProviders(<RemixStub initialEntries={["/app"]} />);
    const explorer = await screen.findByTestId("file-explorer");

    const files = within(explorer).getAllByTestId("tree-node");
    // request mocked with msw
    expect(files).toHaveLength(3);
  });

  it("should open a file", async () => {
    const user = userEvent.setup();
    renderWithProviders(<RemixStub initialEntries={["/app"]} />);
    const explorer = await screen.findByTestId("file-explorer");

    const files = within(explorer).getAllByTestId("tree-node");
    await user.click(files[0]);

    // check if the file is opened
    expect(
      screen.queryByTestId("code-editor-empty-message"),
    ).not.toBeInTheDocument();
    const editor = await screen.findByTestId("code-editor");
    expect(
      within(editor).getByText(/content of file1.ts/i),
    ).toBeInTheDocument();
  });
});
