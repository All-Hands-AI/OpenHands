import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { renderWithProviders } from "test-utils";
import { createRoutesStub } from "react-router";
import { Sidebar } from "#/components/features/sidebar/sidebar";
import { MULTI_CONVERSATION_UI } from "#/utils/feature-flags";

const renderSidebar = () => {
  const RouterStub = createRoutesStub([
    {
      path: "/conversation/:conversationId",
      Component: Sidebar,
    },
  ]);

  renderWithProviders(<RouterStub initialEntries={["/conversation/123"]} />);
};

describe("Sidebar", () => {
  it.skipIf(!MULTI_CONVERSATION_UI)(
    "should have the conversation panel open by default",
    () => {
      renderSidebar();
      expect(screen.getByTestId("conversation-panel")).toBeInTheDocument();
    },
  );

  it.skipIf(!MULTI_CONVERSATION_UI)(
    "should toggle the conversation panel",
    async () => {
      const user = userEvent.setup();
      renderSidebar();

      const projectPanelButton = screen.getByTestId(
        "toggle-conversation-panel",
      );

      await user.click(projectPanelButton);

      expect(
        screen.queryByTestId("conversation-panel"),
      ).not.toBeInTheDocument();
    },
  );
});
