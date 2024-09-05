import { createRemixStub } from "@remix-run/testing";
import { describe, expect, it } from "vitest";
import { screen, within } from "@testing-library/react";
import { renderWithProviders } from "test-utils";
import CodeEditor from "#/routes/app._index";

const RemixStub = createRemixStub([{ path: "/app", Component: CodeEditor }]);

describe("CodeEditor", () => {
  it("should render", async () => {
    renderWithProviders(<RemixStub initialEntries={["/app"]} />);
    await screen.findByTestId("file-explorer");
  });

  it("should retrieve the files", async () => {
    renderWithProviders(<RemixStub initialEntries={["/app"]} />);
    const explorer = await screen.findByTestId("file-explorer");

    const files = within(explorer).getAllByTestId("tree-node");
    // request mocked with msw
    expect(files).toHaveLength(3);
  });

  it.todo("should open a file", async () => {});
});
