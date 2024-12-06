import { render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, test, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { formatTimeDelta } from "#/utils/format-time-delta";
import { ConversationCard } from "#/components/features/conversation-panel/conversation-card";

describe("ConversationCard", () => {
  const onClick = vi.fn();
  const onDelete = vi.fn();
  const onChangeTitle = vi.fn();

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render the conversation card", () => {
    render(
      <ConversationCard
        onDelete={onDelete}
        onClick={onClick}
        onChangeTitle={onChangeTitle}
        name="Conversation 1"
        repo={null}
        lastUpdated="2021-10-01T12:00:00Z"
      />,
    );
    const expectedDate = `${formatTimeDelta(new Date("2021-10-01T12:00:00Z"))} ago`;

    const card = screen.getByTestId("conversation-card");
    const title = within(card).getByTestId("conversation-card-title");

    expect(title).toHaveValue("Conversation 1");
    within(card).getByText(expectedDate);
  });

  it("should render the repo if available", () => {
    const { rerender } = render(
      <ConversationCard
        onDelete={onDelete}
        onClick={onClick}
        onChangeTitle={onChangeTitle}
        name="Conversation 1"
        repo={null}
        lastUpdated="2021-10-01T12:00:00Z"
      />,
    );

    expect(
      screen.queryByTestId("conversation-card-repo"),
    ).not.toBeInTheDocument();

    rerender(
      <ConversationCard
        onDelete={onDelete}
        onClick={onClick}
        onChangeTitle={onChangeTitle}
        name="Conversation 1"
        repo="org/repo"
        lastUpdated="2021-10-01T12:00:00Z"
      />,
    );

    screen.getByTestId("conversation-card-repo");
  });

  it("should call onClick when the card is clicked", async () => {
    const user = userEvent.setup();
    render(
      <ConversationCard
        onDelete={onDelete}
        onClick={onClick}
        onChangeTitle={onChangeTitle}
        name="Conversation 1"
        repo={null}
        lastUpdated="2021-10-01T12:00:00Z"
      />,
    );

    const card = screen.getByTestId("conversation-card");
    await user.click(card);

    expect(onClick).toHaveBeenCalled();
  });

  it("should toggle a context menu when clicking the ellipsis button", async () => {
    const user = userEvent.setup();
    render(
      <ConversationCard
        onDelete={onDelete}
        onClick={onClick}
        onChangeTitle={onChangeTitle}
        name="Conversation 1"
        repo={null}
        lastUpdated="2021-10-01T12:00:00Z"
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
    render(
      <ConversationCard
        onClick={onClick}
        onDelete={onDelete}
        onChangeTitle={onChangeTitle}
        name="Conversation 1"
        repo={null}
        lastUpdated="2021-10-01T12:00:00Z"
      />,
    );

    const ellipsisButton = screen.getByTestId("ellipsis-button");
    await user.click(ellipsisButton);

    const menu = screen.getByTestId("context-menu");
    const deleteButton = within(menu).getByTestId("delete-button");

    await user.click(deleteButton);

    expect(onDelete).toHaveBeenCalled();
  });

  test("clicking the repo should not trigger the onClick handler", async () => {
    const user = userEvent.setup();
    render(
      <ConversationCard
        onClick={onClick}
        onDelete={onDelete}
        onChangeTitle={onChangeTitle}
        name="Conversation 1"
        repo="org/repo"
        lastUpdated="2021-10-01T12:00:00Z"
      />,
    );

    const repo = screen.getByTestId("conversation-card-repo");
    await user.click(repo);

    expect(onClick).not.toHaveBeenCalled();
  });

  test("conversation title should call onChangeTitle when changed and blurred", async () => {
    const user = userEvent.setup();
    render(
      <ConversationCard
        onClick={onClick}
        onDelete={onDelete}
        name="Conversation 1"
        repo={null}
        lastUpdated="2021-10-01T12:00:00Z"
        onChangeTitle={onChangeTitle}
      />,
    );

    const title = screen.getByTestId("conversation-card-title");

    await user.clear(title);
    await user.type(title, "New Conversation Name   ");
    await user.tab();

    expect(onChangeTitle).toHaveBeenCalledWith("New Conversation Name");
    expect(title).toHaveValue("New Conversation Name");
  });

  it("should reset title and not call onChangeTitle when the title is empty", async () => {
    const user = userEvent.setup();
    render(
      <ConversationCard
        onClick={onClick}
        onDelete={onDelete}
        onChangeTitle={onChangeTitle}
        name="Conversation 1"
        repo={null}
        lastUpdated="2021-10-01T12:00:00Z"
      />,
    );

    const title = screen.getByTestId("conversation-card-title");

    await user.clear(title);
    await user.tab();

    expect(onChangeTitle).not.toHaveBeenCalled();
    expect(title).toHaveValue("Conversation 1");
  });

  test("clicking the title should not trigger the onClick handler", async () => {
    const user = userEvent.setup();
    render(
      <ConversationCard
        onClick={onClick}
        onDelete={onDelete}
        onChangeTitle={onChangeTitle}
        name="Conversation 1"
        repo={null}
        lastUpdated="2021-10-01T12:00:00Z"
      />,
    );

    const title = screen.getByTestId("conversation-card-title");
    await user.click(title);

    expect(onClick).not.toHaveBeenCalled();
  });

  test("clicking the delete button should not trigger the onClick handler", async () => {
    const user = userEvent.setup();
    render(
      <ConversationCard
        onClick={onClick}
        onDelete={onDelete}
        onChangeTitle={onChangeTitle}
        name="Conversation 1"
        repo={null}
        lastUpdated="2021-10-01T12:00:00Z"
      />,
    );

    const ellipsisButton = screen.getByTestId("ellipsis-button");
    await user.click(ellipsisButton);

    const menu = screen.getByTestId("context-menu");
    const deleteButton = within(menu).getByTestId("delete-button");

    await user.click(deleteButton);

    expect(onClick).not.toHaveBeenCalled();
  });

  describe("state indicator", () => {
    it("should render the 'cold' indicator by default", () => {
      render(
        <ConversationCard
          onClick={onClick}
          onDelete={onDelete}
          onChangeTitle={onChangeTitle}
          name="Conversation 1"
          repo={null}
          lastUpdated="2021-10-01T12:00:00Z"
        />,
      );

      screen.getByTestId("cold-indicator");
    });

    it("should render the other indicators when provided", () => {
      render(
        <ConversationCard
          onClick={onClick}
          onDelete={onDelete}
          onChangeTitle={onChangeTitle}
          name="Conversation 1"
          repo={null}
          lastUpdated="2021-10-01T12:00:00Z"
          state="warm"
        />,
      );

      expect(screen.queryByTestId("cold-indicator")).not.toBeInTheDocument();
      screen.getByTestId("warm-indicator");
    });
  });
});
