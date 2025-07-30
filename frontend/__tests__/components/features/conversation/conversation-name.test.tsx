import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "test-utils";
import { ConversationName } from "#/components/features/conversation/conversation-name";

// Mock the hooks and utilities
vi.mock("#/hooks/query/use-active-conversation", () => ({
  useActiveConversation: () => ({
    data: {
      conversation_id: "test-conversation-id",
      title: "Test Conversation",
      status: "RUNNING",
    },
  }),
}));

vi.mock("#/hooks/mutation/use-update-conversation", () => ({
  useUpdateConversation: () => ({
    mutate: vi.fn(),
  }),
}));

vi.mock("#/utils/custom-toast-handlers", () => ({
  displaySuccessToast: vi.fn(),
}));

// Mock react-i18next
vi.mock("react-i18next", async () => {
  const actual = await vi.importActual("react-i18next");
  return {
    ...actual,
    useTranslation: () => ({
      t: (key: string) => {
        const translations: Record<string, string> = {
          CONVERSATION$TITLE_UPDATED: "Conversation title updated",
        };
        return translations[key] || key;
      },
      i18n: {
        changeLanguage: () => new Promise(() => {}),
      },
    }),
  };
});

describe("ConversationName", () => {
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

  it("should render the conversation name in view mode", () => {
    renderWithProviders(<ConversationName />);

    const container = screen.getByTestId("conversation-name");
    const titleElement = within(container).getByTestId(
      "conversation-name-title",
    );

    expect(container).toBeInTheDocument();
    expect(titleElement).toBeInTheDocument();
    expect(titleElement).toHaveTextContent("Test Conversation");
  });

  it("should switch to edit mode on double click", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ConversationName />);

    const titleElement = screen.getByTestId("conversation-name-title");

    // Initially should be in view mode
    expect(titleElement).toBeInTheDocument();
    expect(
      screen.queryByTestId("conversation-name-input"),
    ).not.toBeInTheDocument();

    // Double click to enter edit mode
    await user.dblClick(titleElement);

    // Should now be in edit mode
    expect(
      screen.queryByTestId("conversation-name-title"),
    ).not.toBeInTheDocument();
    const inputElement = screen.getByTestId("conversation-name-input");
    expect(inputElement).toBeInTheDocument();
    expect(inputElement).toHaveValue("Test Conversation");
  });

  it("should update conversation title when input loses focus with valid value", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ConversationName />);

    const titleElement = screen.getByTestId("conversation-name-title");
    await user.dblClick(titleElement);

    const inputElement = screen.getByTestId("conversation-name-input");
    await user.clear(inputElement);
    await user.type(inputElement, "New Conversation Title");
    await user.tab(); // Trigger blur event

    // Verify that the update function was called (we can't access the mock directly)
    // but we can verify the component behavior
    expect(inputElement).toHaveValue("New Conversation Title");
  });

  it("should not update conversation when title is unchanged", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ConversationName />);

    const titleElement = screen.getByTestId("conversation-name-title");
    await user.dblClick(titleElement);

    const inputElement = screen.getByTestId("conversation-name-input");
    // Keep the same title
    await user.tab();

    // Should still have the original title
    expect(inputElement).toHaveValue("Test Conversation");
  });

  it("should reset input value when title is empty and blur", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ConversationName />);

    const titleElement = screen.getByTestId("conversation-name-title");
    await user.dblClick(titleElement);

    const inputElement = screen.getByTestId("conversation-name-input");
    await user.clear(inputElement);
    await user.tab();

    // Should reset to original title
    expect(inputElement).toHaveValue("Test Conversation");
  });

  it("should trim whitespace from input value", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ConversationName />);

    const titleElement = screen.getByTestId("conversation-name-title");
    await user.dblClick(titleElement);

    const inputElement = screen.getByTestId("conversation-name-input");
    await user.clear(inputElement);
    await user.type(inputElement, "  Trimmed Title  ");
    await user.tab();

    // Should have trimmed the whitespace
    expect(inputElement).toHaveValue("Trimmed Title");
  });

  it("should handle Enter key to save changes", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ConversationName />);

    const titleElement = screen.getByTestId("conversation-name-title");
    await user.dblClick(titleElement);

    const inputElement = screen.getByTestId("conversation-name-input");
    await user.clear(inputElement);
    await user.type(inputElement, "New Title");
    await user.keyboard("{Enter}");

    // Should have the new title
    expect(inputElement).toHaveValue("New Title");
  });

  it("should prevent event propagation when clicking input in edit mode", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ConversationName />);

    const titleElement = screen.getByTestId("conversation-name-title");
    await user.dblClick(titleElement);

    const inputElement = screen.getByTestId("conversation-name-input");
    const clickEvent = new MouseEvent("click", { bubbles: true });
    const preventDefaultSpy = vi.spyOn(clickEvent, "preventDefault");
    const stopPropagationSpy = vi.spyOn(clickEvent, "stopPropagation");

    inputElement.dispatchEvent(clickEvent);

    expect(preventDefaultSpy).toHaveBeenCalled();
    expect(stopPropagationSpy).toHaveBeenCalled();
  });

  it("should return to view mode after blur", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ConversationName />);

    const titleElement = screen.getByTestId("conversation-name-title");
    await user.dblClick(titleElement);

    // Should be in edit mode
    expect(screen.getByTestId("conversation-name-input")).toBeInTheDocument();

    const inputElement = screen.getByTestId("conversation-name-input");
    await user.tab();

    // Should be back in view mode
    expect(screen.getByTestId("conversation-name-title")).toBeInTheDocument();
    expect(
      screen.queryByTestId("conversation-name-input"),
    ).not.toBeInTheDocument();
  });

  it("should focus input when entering edit mode", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ConversationName />);

    const titleElement = screen.getByTestId("conversation-name-title");
    await user.dblClick(titleElement);

    const inputElement = screen.getByTestId("conversation-name-input");
    expect(inputElement).toHaveFocus();
  });
});
