import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "test-utils";
import { Messages } from "#/components/features/chat/messages";
import { Message } from "#/message";

const testTimestamp = "2025-03-24T15:30:00Z";
const testTimestampNoZ = "2025-03-24T15:30:00";

describe("Messages Component", () => {
  it("should correctly format timestamp with Z in UTC Time Zone", async () => {
    const messages: Message[] = [
      {
        content: "Message with Z",
        sender: "assistant",
        timestamp: testTimestamp,
        type: "thought",
      },
    ];

    renderWithProviders(
      <Messages messages={messages} isAwaitingUserConfirmation={false} />,
    );
    expect(await screen.findByText("03/24 15:30")).toBeInTheDocument();
  });

  it("should correctly format timestamp without Z in UTC Time Zone", async () => {
    const messages: Message[] = [
      {
        content: "Message without Z",
        sender: "assistant",
        timestamp: testTimestampNoZ,
        type: "thought",
      },
    ];

    renderWithProviders(
      <Messages messages={messages} isAwaitingUserConfirmation={false} />,
    );
    expect(await screen.findByText("03/24 15:30")).toBeInTheDocument();
  });

  it("should correctly format timestamp with invalid timestamp", async () => {
    const messages: Message[] = [
      {
        content: "Message with invalid timestamp",
        sender: "assistant",
        timestamp: "",
        type: "thought",
      },
    ];

    renderWithProviders(
      <Messages messages={messages} isAwaitingUserConfirmation={false} />,
    );
    expect(await screen.findByText("N/A")).toBeInTheDocument();
  });

  it("should correctly format timestamp without timestamp", async () => {
    const messages: Message[] = [
      {
        content: "Message without timestamp",
        sender: "assistant",
        timestamp: "",
        type: "thought",
      },
    ];

    renderWithProviders(
      <Messages messages={messages} isAwaitingUserConfirmation={false} />,
    );
    expect(await screen.findByText("N/A")).toBeInTheDocument();
  });

  it("should return null when message content is null or empty", async () => {
    const messages: Message[] = [
      {
        content: "",
        sender: "assistant",
        timestamp: testTimestamp,
        type: "thought",
      },
      {
        content: null as unknown as string,
        sender: "assistant",
        timestamp: testTimestamp,
        type: "thought",
      },
      {
        content: undefined as unknown as string,
        sender: "assistant",
        timestamp: testTimestamp,
        type: "thought",
      },
    ];

    const { container } = renderWithProviders(
      <Messages messages={messages} isAwaitingUserConfirmation={false} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("should display 'N/A' when timestamp is missing", async () => {
    const messages: Message[] = [
      {
        content: "No timestamp",
        sender: "assistant",
        timestamp: "",
        type: "thought",
      },
      {
        content: "Null timestamp",
        sender: "assistant",
        timestamp: null as unknown as string,
        type: "thought",
      },
      {
        content: "Undefined timestamp",
        sender: "assistant",
        timestamp: undefined as unknown as string,
        type: "thought",
      },
    ];

    renderWithProviders(
      <Messages messages={messages} isAwaitingUserConfirmation={false} />,
    );
    expect(await screen.findAllByText("N/A")).toHaveLength(3);
  });

  it("should correctly format timestamp when sender is user and timestamp is missing", async () => {
    const messages: Message[] = [
      {
        content: "User timestamp missing",
        sender: "user",
        timestamp: "",
        type: "thought",
      },
    ];

    renderWithProviders(
      <Messages messages={messages} isAwaitingUserConfirmation={false} />,
    );
    expect(
      await screen.findByText("User timestamp missing"),
    ).toBeInTheDocument();
    expect(await screen.findByText("N/A")).toBeInTheDocument();
  });

  it("should render agent info when agentname is provided", async () => {
    const messages: Message[] = [
      {
        content: "Agent message",
        sender: "assistant",
        timestamp: testTimestampNoZ,
        agentName: "TestAgent@host",
        type: "thought",
      },
    ];

    renderWithProviders(
      <Messages messages={messages} isAwaitingUserConfirmation={false} />,
    );
    expect(await screen.findByText(/TestAgent@host/i)).toBeInTheDocument();
  });

  it("should render agent info when agentname is provided (timestamp endsWith('Z') === false)", async () => {
    const messages: Message[] = [
      {
        content: "Agent message without Z",
        sender: "assistant",
        timestamp: testTimestampNoZ,
        agentName: "TestAgent@host",
        type: "thought",
      },
    ];

    renderWithProviders(
      <Messages messages={messages} isAwaitingUserConfirmation={false} />,
    );

    const agentInfo = screen
      .getByText(/TestAgent@host/i)
      .closest(".agent-info");
    expect(agentInfo).toBeInTheDocument();
    expect(await screen.findByText(/TestAgent@host/i)).toBeInTheDocument();
  });

  it("should correctly format timestamp when sender is assistant and timestamp is missing", async () => {
    const messages: Message[] = [
      {
        content: "Assistant timestamp missing",
        sender: "assistant",
        timestamp: "",
        type: "thought",
      },
    ];

    renderWithProviders(
      <Messages messages={messages} isAwaitingUserConfirmation={false} />,
    );
    expect(
      await screen.findByText("Assistant timestamp missing"),
    ).toBeInTheDocument();
    expect(await screen.findByText("N/A")).toBeInTheDocument();
  });

  it("should render image carousel when imageUrls are present", async () => {
    const messages: Message[] = [
      {
        content: "Message with images",
        sender: "assistant",
        timestamp: testTimestamp,
        imageUrls: ["image1.jpg", "image2.jpg"],
        type: "thought",
      },
    ];

    renderWithProviders(
      <Messages messages={messages} isAwaitingUserConfirmation={false} />,
    );

    const images = await screen.findAllByRole("img");
    expect(images.length).toBe(2);
  });

  it("should render ConfirmationButtons when awaiting user confirmation", async () => {
    const messages: Message[] = [
      {
        content: "Needs confirmation",
        sender: "assistant",
        timestamp: testTimestamp,
        type: "thought",
      },
    ];

    renderWithProviders(
      <Messages messages={messages} isAwaitingUserConfirmation />,
    );
    expect(
      await screen.findByRole("button", { name: /confirm/i }),
    ).toBeInTheDocument();
  });

  it("should correctly format timestamp when sender is user and timestamp is missing", async () => {
    const messages: Message[] = [
      {
        content: "User timestamp missing",
        sender: "user",
        timestamp: "",
        type: "thought",
      },
    ];

    renderWithProviders(
      <Messages messages={messages} isAwaitingUserConfirmation={false} />,
    );
    expect(
      await screen.findByText("User timestamp missing"),
    ).toBeInTheDocument();
    expect(await screen.findByText("N/A")).toBeInTheDocument();
  });

  it("should render user-time div when sender is user", async () => {
    const messages: Message[] = [
      {
        content: "User message",
        sender: "user",
        timestamp: testTimestamp,
        type: "thought",
      },
    ];

    renderWithProviders(
      <Messages messages={messages} isAwaitingUserConfirmation={false} />,
    );
    expect(await screen.findByText("User message")).toBeInTheDocument();
  });
});
