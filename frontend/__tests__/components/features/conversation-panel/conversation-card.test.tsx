import { prettyDOM, screen, within } from "@testing-library/react";
import {
  afterAll,
  afterEach,
  beforeAll,
  describe,
  expect,
  it,
  test,
  vi,
} from "vitest";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "test-utils";
import { formatTimeDelta } from "#/utils/format-time-delta";
import { ConversationCard } from "#/components/features/conversation-panel/conversation-card/conversation-card";
import { clickOnEditButton } from "./utils";
import { act } from "react";

// We'll use the actual i18next implementation but override the translation function

// Mock the t function to return our custom translations
vi.mock("react-i18next", async () => {
  const actual = await vi.importActual("react-i18next");
  return {
    ...actual,
    useTranslation: () => ({
      t: (key: string) => {
        const translations: Record<string, string> = {
          CONVERSATION$CREATED: "Created",
          CONVERSATION$AGO: "ago",
          CONVERSATION$UPDATED: "Updated",
        };
        return translations[key] || key;
      },
      i18n: {
        changeLanguage: () => new Promise(() => {}),
      },
    }),
  };
});

describe("ConversationCard", () => {
  const onClick = vi.fn();
  const onDelete = vi.fn();
  const onChangeTitle = vi.fn();

  beforeAll(() => {
    vi.stubGlobal("window", {
      open: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  afterAll(() => {
    vi.unstubAllGlobals();
  });

  it("should render the conversation card", () => {
    renderWithProviders(
      <ConversationCard
        onDelete={onDelete}
        onChangeTitle={onChangeTitle}
        isActive
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
      />,
    );

    const card = screen.getByTestId("conversation-card");

    within(card).getByText("Conversation 1");

    // Just check that the card contains the expected text content
    expect(card).toHaveTextContent("ago");

    // Use a regex to match the time part since it might have whitespace
    const timeRegex = new RegExp(
      formatTimeDelta(new Date("2021-10-01T12:00:00Z")),
    );
    expect(card).toHaveTextContent(timeRegex);
  });

  it("should render the selectedRepository if available", () => {
    const { rerender } = renderWithProviders(
      <ConversationCard
        onDelete={onDelete}
        onChangeTitle={onChangeTitle}
        isActive
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
      />,
    );

    expect(
      screen.queryByTestId("conversation-card-selected-repository"),
    ).not.toBeInTheDocument();

    rerender(
      <ConversationCard
        onDelete={onDelete}
        onChangeTitle={onChangeTitle}
        isActive
        title="Conversation 1"
        selectedRepository={{
          selected_repository: "org/selectedRepository",
          selected_branch: "main",
          git_provider: "github",
        }}
        lastUpdatedAt="2021-10-01T12:00:00Z"
      />,
    );

    screen.getByTestId("conversation-card-selected-repository");
  });

  it("should toggle a context menu when clicking the ellipsis button", async () => {
    const user = userEvent.setup();
    const onContextMenuToggle = vi.fn();
    const { rerender } = renderWithProviders(
      <ConversationCard
        onDelete={onDelete}
        onChangeTitle={onChangeTitle}
        isActive
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
        contextMenuOpen={false}
        onContextMenuToggle={onContextMenuToggle}
      />,
    );

    expect(screen.queryByTestId("context-menu")).not.toBeInTheDocument();

    const ellipsisButton = screen.getByTestId("ellipsis-button");
    await user.click(ellipsisButton);

    expect(onContextMenuToggle).toHaveBeenCalledWith(true);

    // Simulate context menu being opened by parent
    rerender(
      <ConversationCard
        onDelete={onDelete}
        onChangeTitle={onChangeTitle}
        isActive
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
        contextMenuOpen
        onContextMenuToggle={onContextMenuToggle}
      />,
    );

    screen.getByTestId("context-menu");

    await user.click(ellipsisButton);

    expect(onContextMenuToggle).toHaveBeenCalledWith(false);
  });

  it("should call onDelete when the delete button is clicked", async () => {
    const user = userEvent.setup();
    const onContextMenuToggle = vi.fn();
    renderWithProviders(
      <ConversationCard
        onDelete={onDelete}
        isActive
        onChangeTitle={onChangeTitle}
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
        contextMenuOpen
        onContextMenuToggle={onContextMenuToggle}
      />,
    );

    const menu = screen.getByTestId("context-menu");
    const deleteButton = within(menu).getByTestId("delete-button");

    await user.click(deleteButton);

    expect(onDelete).toHaveBeenCalled();
    expect(onContextMenuToggle).toHaveBeenCalledWith(false);
  });

  test("clicking the selectedRepository should not trigger the onClick handler", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <ConversationCard
        onDelete={onDelete}
        isActive
        onChangeTitle={onChangeTitle}
        title="Conversation 1"
        selectedRepository={{
          selected_repository: "org/selectedRepository",
          selected_branch: "main",
          git_provider: "github",
        }}
        lastUpdatedAt="2021-10-01T12:00:00Z"
      />,
    );

    const selectedRepository = screen.getByTestId(
      "conversation-card-selected-repository",
    );
    await user.click(selectedRepository);

    expect(onClick).not.toHaveBeenCalled();
  });

  test("conversation title should call onChangeTitle when changed and blurred", async () => {
    const user = userEvent.setup();
    let menuOpen = true;
    const onContextMenuToggle = vi.fn((isOpen: boolean) => {
      menuOpen = isOpen;
    });
    const { rerender } = renderWithProviders(
      <ConversationCard
        onDelete={onDelete}
        isActive
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
        onChangeTitle={onChangeTitle}
        contextMenuOpen={menuOpen}
        onContextMenuToggle={onContextMenuToggle}
      />,
    );

    await clickOnEditButton(user);

    // Re-render with updated state
    rerender(
      <ConversationCard
        onDelete={onDelete}
        isActive
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
        onChangeTitle={onChangeTitle}
        contextMenuOpen={menuOpen}
        onContextMenuToggle={onContextMenuToggle}
      />,
    );

    const title = screen.getByTestId("conversation-card-title");

    expect(title).toBeEnabled();
    expect(screen.queryByTestId("context-menu")).not.toBeInTheDocument();
    // expect to be focused
    expect(document.activeElement).toBe(title);

    await user.clear(title);
    await user.type(title, "New Conversation Name   ");
    await user.tab();

    expect(onChangeTitle).toHaveBeenCalledWith("New Conversation Name");
  });

  it("should not call onChange title", async () => {
    const user = userEvent.setup();
    const onContextMenuToggle = vi.fn();
    renderWithProviders(
      <ConversationCard
        onDelete={onDelete}
        isActive
        onChangeTitle={onChangeTitle}
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
        contextMenuOpen
        onContextMenuToggle={onContextMenuToggle}
      />,
    );

    await clickOnEditButton(user);

    const title = screen.getByTestId("conversation-card-title");

    await user.clear(title);
    await user.tab();

    expect(onChangeTitle).not.toBeCalled();
  });

  test("clicking the title should trigger the onClick handler", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <ConversationCard
        onClick={onClick}
        onDelete={onDelete}
        isActive
        onChangeTitle={onChangeTitle}
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
      />,
    );

    const title = screen.getByTestId("conversation-card-title");
    await user.click(title);

    expect(onClick).toHaveBeenCalled();
  });

  test("clicking the title should not trigger the onClick handler if edit mode", async () => {
    const user = userEvent.setup();
    const onContextMenuToggle = vi.fn();
    renderWithProviders(
      <ConversationCard
        onDelete={onDelete}
        isActive
        onChangeTitle={onChangeTitle}
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
        contextMenuOpen
        onContextMenuToggle={onContextMenuToggle}
      />,
    );

    await clickOnEditButton(user);

    const title = screen.getByTestId("conversation-card-title");
    await user.click(title);

    expect(onClick).not.toHaveBeenCalled();
  });

  test("clicking the delete button should not trigger the onClick handler", async () => {
    const user = userEvent.setup();
    const onContextMenuToggle = vi.fn();
    renderWithProviders(
      <ConversationCard
        onDelete={onDelete}
        isActive
        onChangeTitle={onChangeTitle}
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
        contextMenuOpen
        onContextMenuToggle={onContextMenuToggle}
      />,
    );

    const menu = screen.getByTestId("context-menu");
    const deleteButton = within(menu).getByTestId("delete-button");

    await user.click(deleteButton);

    expect(onClick).not.toHaveBeenCalled();
  });

  it("should show display cost button only when showOptions is true", async () => {
    const onContextMenuToggle = vi.fn();
    const { rerender } = renderWithProviders(
      <ConversationCard
        onDelete={onDelete}
        onChangeTitle={onChangeTitle}
        isActive
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
        contextMenuOpen
        onContextMenuToggle={onContextMenuToggle}
      />,
    );

    // Wait for context menu to appear
    const menu = await screen.findByTestId("context-menu");
    expect(
      within(menu).queryByTestId("display-cost-button"),
    ).not.toBeInTheDocument();

    rerender(
      <ConversationCard
        onDelete={onDelete}
        onChangeTitle={onChangeTitle}
        showOptions
        isActive
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
        contextMenuOpen
        onContextMenuToggle={onContextMenuToggle}
      />,
    );

    // Wait for context menu to appear and check for display cost button
    const newMenu = await screen.findByTestId("context-menu");
    within(newMenu).getByTestId("display-cost-button");
  });

  it("should show metrics modal when clicking the display cost button", async () => {
    const user = userEvent.setup();
    const onContextMenuToggle = vi.fn();
    renderWithProviders(
      <ConversationCard
        onDelete={onDelete}
        isActive
        onChangeTitle={onChangeTitle}
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
        showOptions
        contextMenuOpen
        onContextMenuToggle={onContextMenuToggle}
      />,
    );

    const menu = screen.getByTestId("context-menu");
    const displayCostButton = within(menu).getByTestId("display-cost-button");

    await user.click(displayCostButton);

    // Verify if metrics modal is displayed by checking for the modal content
    expect(screen.getByTestId("metrics-modal")).toBeInTheDocument();
  });

  it("should not display the edit or delete options if the handler is not provided", async () => {
    const onContextMenuToggle = vi.fn();
    const { rerender } = renderWithProviders(
      <ConversationCard
        onClick={onClick}
        onChangeTitle={onChangeTitle}
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
        contextMenuOpen
        onContextMenuToggle={onContextMenuToggle}
      />,
    );

    const menu = await screen.findByTestId("context-menu");
    expect(within(menu).queryByTestId("edit-button")).toBeInTheDocument();
    expect(within(menu).queryByTestId("delete-button")).not.toBeInTheDocument();

    rerender(
      <ConversationCard
        onClick={onClick}
        onDelete={onDelete}
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
        contextMenuOpen
        onContextMenuToggle={onContextMenuToggle}
      />,
    );

    const newMenu = await screen.findByTestId("context-menu");
    expect(
      within(newMenu).queryByTestId("edit-button"),
    ).not.toBeInTheDocument();
    expect(within(newMenu).queryByTestId("delete-button")).toBeInTheDocument();
  });

  it("should not render the ellipsis button if there are no actions", () => {
    const { rerender } = renderWithProviders(
      <ConversationCard
        onClick={onClick}
        onDelete={onDelete}
        onChangeTitle={onChangeTitle}
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
      />,
    );

    expect(screen.getByTestId("ellipsis-button")).toBeInTheDocument();

    rerender(
      <ConversationCard
        onClick={onClick}
        onDelete={onDelete}
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
      />,
    );

    expect(screen.getByTestId("ellipsis-button")).toBeInTheDocument();

    rerender(
      <ConversationCard
        onClick={onClick}
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
      />,
    );

    expect(screen.queryByTestId("ellipsis-button")).not.toBeInTheDocument();
  });
});
