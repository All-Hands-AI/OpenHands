import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ConversationOverviewDrawerContent } from "#/components/features/conversation/conversation-overview-drawer-content";
import {
  ConversationOverviewDrawerProvider,
  useConversationOverviewDrawer,
} from "#/components/features/conversation/conversation-overview-drawer-context";
import { CONVERSATION_OVERVIEW_DRAWER_SECTION } from "#/components/features/conversation/conversation-overview-drawer.types";
import { useCloseOnEscape } from "#/hooks/use-close-on-escape";

vi.mock("#/hooks/use-conversation-overview-stats", () => ({
  useConversationOverviewStats: () => ({
    workspaceName: "demo",
  }),
}));

vi.mock("#/hooks/use-conversation-primary-repository", () => ({
  useConversationPrimaryRepository: () => ({
    repository: "openhands/agent-canvas",
    provider: "github" as const,
    branch: "main",
    isConnected: true,
  }),
}));

vi.mock("#/hooks/query/use-repository-git-items", () => ({
  useRepositoryPullRequests: () => ({
    data: [],
    isLoading: false,
    isError: false,
  }),
  useRepositoryIssues: () => ({
    data: [],
    isLoading: false,
    isError: false,
  }),
}));

function OpenSection({
  section,
}: {
  section: (typeof CONVERSATION_OVERVIEW_DRAWER_SECTION)[keyof typeof CONVERSATION_OVERVIEW_DRAWER_SECTION];
}) {
  const { openSection } = useConversationOverviewDrawer();
  return (
    <button
      type="button"
      data-testid="open-drawer-section"
      onClick={() => openSection(section)}
    >
      Open
    </button>
  );
}

// Stands in for a menu that closes on Escape, such as the Overview ⋯ menu.
function MenuOverDrawer() {
  const [isOpen, setIsOpen] = React.useState(false);
  useCloseOnEscape(isOpen, () => setIsOpen(false));
  return (
    <>
      <button
        type="button"
        data-testid="open-menu-over-drawer"
        onClick={() => setIsOpen(true)}
      >
        Menu
      </button>
      {isOpen ? <div data-testid="menu-over-drawer" /> : null}
    </>
  );
}

function renderDrawer(
  section: (typeof CONVERSATION_OVERVIEW_DRAWER_SECTION)[keyof typeof CONVERSATION_OVERVIEW_DRAWER_SECTION],
) {
  return render(
    <ConversationOverviewDrawerProvider>
      <OpenSection section={section} />
      <MenuOverDrawer />
      <ConversationOverviewDrawerContent />
    </ConversationOverviewDrawerProvider>,
    {
      wrapper: ({ children }) => (
        <QueryClientProvider
          client={
            new QueryClient({
              defaultOptions: { queries: { retry: false } },
            })
          }
        >
          {children}
        </QueryClientProvider>
      ),
    },
  );
}

describe("ConversationOverviewDrawerContent", () => {
  it("places the close button left of the title", async () => {
    const user = userEvent.setup();
    renderDrawer(CONVERSATION_OVERVIEW_DRAWER_SECTION.pull_requests);

    await user.click(screen.getByTestId("open-drawer-section"));

    const header = screen
      .getByTestId("conversation-overview-drawer-content")
      .querySelector("header");
    expect(header).not.toBeNull();
    expect(header).toHaveClass("h-10");
    expect(header).toHaveClass("min-h-10");
    expect(header).toHaveClass("pr-4");
    const closeButton = within(header as HTMLElement).getByTestId(
      "conversation-overview-drawer-close",
    );
    const title = within(header as HTMLElement).getByRole("heading");
    expect(
      closeButton.compareDocumentPosition(title) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });

  it("lets a menu opened over the drawer take the first Escape", async () => {
    const user = userEvent.setup();
    renderDrawer(CONVERSATION_OVERVIEW_DRAWER_SECTION.pull_requests);

    await user.click(screen.getByTestId("open-drawer-section"));
    await user.click(screen.getByTestId("open-menu-over-drawer"));

    await user.keyboard("{Escape}");
    expect(screen.queryByTestId("menu-over-drawer")).not.toBeInTheDocument();
    expect(
      screen.getByTestId("conversation-overview-drawer-content"),
    ).toBeInTheDocument();

    await user.keyboard("{Escape}");
    expect(
      screen.queryByTestId("conversation-overview-drawer-content"),
    ).not.toBeInTheDocument();
  });

  it("places the view-on-provider link in the header for pull requests", async () => {
    const user = userEvent.setup();
    renderDrawer(CONVERSATION_OVERVIEW_DRAWER_SECTION.pull_requests);

    await user.click(screen.getByTestId("open-drawer-section"));

    const header = screen
      .getByTestId("conversation-overview-drawer-content")
      .querySelector("header");
    const externalLink = within(header as HTMLElement).getByTestId(
      "conversation-overview-pull_requests-open-external",
    );

    expect(externalLink).toHaveAttribute(
      "href",
      "https://github.com/openhands/agent-canvas/pulls",
    );
    expect(externalLink).toHaveTextContent(
      "CONVERSATION$OVERVIEW_VIEW_ON_PROVIDER",
    );
    expect(
      screen
        .getByTestId("conversation-overview-pull_requests-panel")
        .querySelector(
          '[data-testid="conversation-overview-pull_requests-open-external"]',
        ),
    ).toBeNull();
  });
});
