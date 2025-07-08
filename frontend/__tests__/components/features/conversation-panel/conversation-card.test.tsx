import { screen, within } from "@testing-library/react";
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
import { ConversationCard } from "#/components/features/conversation-panel/conversation-card";
import { clickOnEditButton } from "./utils";

// We'll use the actual i18next implementation but override the translation function
import { I18nextProvider } from "react-i18next";
import i18n from "i18next";

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
    expect(card).toHaveTextContent("Created");
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

    expect(screen.queryByTestId("context-menu")).not.toBeInTheDocument();

    const ellipsisButton = screen.getByTestId("ellipsis-button");
    await user.click(ellipsisButton);

    screen.getByTestId("context-menu");

    await user.click(ellipsisButton);

    expect(screen.queryByTestId("context-menu")).not.toBeInTheDocument();
  });

  it("should call onDelete when the delete button is clicked", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <ConversationCard
        onDelete={onDelete}
        isActive
        onChangeTitle={onChangeTitle}
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
      />,
    );

    const ellipsisButton = screen.getByTestId("ellipsis-button");
    await user.click(ellipsisButton);

    const menu = screen.getByTestId("context-menu");
    const deleteButton = within(menu).getByTestId("delete-button");

    await user.click(deleteButton);

    expect(onDelete).toHaveBeenCalled();
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
    renderWithProviders(
      <ConversationCard
        onDelete={onDelete}
        isActive
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
        onChangeTitle={onChangeTitle}
      />,
    );

    await clickOnEditButton(user);
    const title = screen.getByTestId("conversation-card-title");

    expect(title).toBeEnabled();
    expect(screen.queryByTestId("context-menu")).not.toBeInTheDocument();
    // expect to be focused
    expect(document.activeElement).toBe(title);

    await user.clear(title);
    await user.type(title, "New Conversation Name   ");
    await user.tab();

    expect(onChangeTitle).toHaveBeenCalledWith("New Conversation Name");
    expect(title).toHaveValue("New Conversation Name");
  });

  it("should reset title and not call onChangeTitle when the title is empty", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <ConversationCard
        onDelete={onDelete}
        isActive
        onChangeTitle={onChangeTitle}
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
      />,
    );

    await clickOnEditButton(user);

    const title = screen.getByTestId("conversation-card-title");

    await user.clear(title);
    await user.tab();

    expect(onChangeTitle).not.toHaveBeenCalled();
    expect(title).toHaveValue("Conversation 1");
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
    renderWithProviders(
      <ConversationCard
        onDelete={onDelete}
        isActive
        onChangeTitle={onChangeTitle}
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
      />,
    );

    await clickOnEditButton(user);

    const title = screen.getByTestId("conversation-card-title");
    await user.click(title);

    expect(onClick).not.toHaveBeenCalled();
  });

  test("clicking the delete button should not trigger the onClick handler", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <ConversationCard
        onDelete={onDelete}
        isActive
        onChangeTitle={onChangeTitle}
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
      />,
    );

    const ellipsisButton = screen.getByTestId("ellipsis-button");
    await user.click(ellipsisButton);

    const menu = screen.getByTestId("context-menu");
    const deleteButton = within(menu).getByTestId("delete-button");

    await user.click(deleteButton);

    expect(onClick).not.toHaveBeenCalled();
  });

  it("should show display cost button only when showOptions is true", async () => {
    const user = userEvent.setup();
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

    const ellipsisButton = screen.getByTestId("ellipsis-button");
    await user.click(ellipsisButton);

    // Wait for context menu to appear
    const menu = await screen.findByTestId("context-menu");
    expect(
      within(menu).queryByTestId("display-cost-button"),
    ).not.toBeInTheDocument();

    // Close menu
    await user.click(ellipsisButton);

    rerender(
      <ConversationCard
        onDelete={onDelete}
        onChangeTitle={onChangeTitle}
        showOptions
        isActive
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
      />,
    );

    // Open menu again
    await user.click(ellipsisButton);

    // Wait for context menu to appear and check for display cost button
    const newMenu = await screen.findByTestId("context-menu");
    within(newMenu).getByTestId("display-cost-button");
  });

  it("should show metrics modal when clicking the display cost button", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <ConversationCard
        onDelete={onDelete}
        isActive
        onChangeTitle={onChangeTitle}
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
        showOptions
      />,
    );

    const ellipsisButton = screen.getByTestId("ellipsis-button");
    await user.click(ellipsisButton);

    const menu = screen.getByTestId("context-menu");
    const displayCostButton = within(menu).getByTestId("display-cost-button");

    await user.click(displayCostButton);

    // Verify if metrics modal is displayed by checking for the modal content
    expect(screen.getByTestId("metrics-modal")).toBeInTheDocument();
  });

  it("should not display the edit or delete options if the handler is not provided", async () => {
    const user = userEvent.setup();
    const { rerender } = renderWithProviders(
      <ConversationCard
        onClick={onClick}
        onChangeTitle={onChangeTitle}
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
      />,
    );

    const ellipsisButton = screen.getByTestId("ellipsis-button");
    await user.click(ellipsisButton);

    const menu = await screen.findByTestId("context-menu");
    expect(within(menu).queryByTestId("edit-button")).toBeInTheDocument();
    expect(within(menu).queryByTestId("delete-button")).not.toBeInTheDocument();

    // toggle to hide the context menu
    await user.click(ellipsisButton);

    rerender(
      <ConversationCard
        onClick={onClick}
        onDelete={onDelete}
        title="Conversation 1"
        selectedRepository={null}
        lastUpdatedAt="2021-10-01T12:00:00Z"
      />,
    );

    await user.click(ellipsisButton);
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

  describe("state indicator", () => {
    it("should render the 'STOPPED' indicator by default", () => {
      renderWithProviders(
        <ConversationCard
          onDelete={onDelete}
          isActive
          onChangeTitle={onChangeTitle}
          title="Conversation 1"
          selectedRepository={null}
          lastUpdatedAt="2021-10-01T12:00:00Z"
        />,
      );

      screen.getByTestId("STOPPED-indicator");
    });

    it("should render the other indicators when provided", () => {
      renderWithProviders(
        <ConversationCard
          onDelete={onDelete}
          isActive
          onChangeTitle={onChangeTitle}
          title="Conversation 1"
          selectedRepository={null}
          lastUpdatedAt="2021-10-01T12:00:00Z"
          conversationStatus="RUNNING"
        />,
      );

      expect(screen.queryByTestId("STOPPED-indicator")).not.toBeInTheDocument();
      screen.getByTestId("RUNNING-indicator");
    });
  });
});
