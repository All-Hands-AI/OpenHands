import { render, screen } from "@testing-library/react";
import { useParams } from "react-router";
import { vi, describe, test, expect, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ChatInterface } from "./chat-interface";
import { useWsClient } from "#/context/ws-client-provider";
import { useOptimisticUserMessage } from "#/hooks/use-optimistic-user-message";
import { useWSErrorMessage } from "#/hooks/use-ws-error-message";
import { useConfig } from "#/hooks/query/use-config";
import { useGetTrajectory } from "#/hooks/mutation/use-get-trajectory";
import { useUploadFiles } from "#/hooks/mutation/use-upload-files";
import { OpenHandsAction } from "#/types/core/actions";

// Mock the hooks
vi.mock("#/context/ws-client-provider");
vi.mock("#/hooks/use-optimistic-user-message");
vi.mock("#/hooks/use-ws-error-message");
vi.mock("react-router");
vi.mock("#/hooks/query/use-config");
vi.mock("#/hooks/mutation/use-get-trajectory");
vi.mock("#/hooks/mutation/use-upload-files");
vi.mock("react-redux", () => ({
  useSelector: vi.fn(() => ({
    curAgentState: "AWAITING_USER_INPUT",
    selectedRepository: null,
    replayJson: null,
  })),
}));

describe("ChatInterface", () => {
  // Create a new QueryClient for each test
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    // Default mock implementations
    (useWsClient as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      send: vi.fn(),
      isLoadingMessages: false,
      parsedEvents: [],
    });
    (
      useOptimisticUserMessage as unknown as ReturnType<typeof vi.fn>
    ).mockReturnValue({
      setOptimisticUserMessage: vi.fn(),
      getOptimisticUserMessage: vi.fn(() => null),
    });
    (useWSErrorMessage as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      getErrorMessage: vi.fn(() => null),
      setErrorMessage: vi.fn(),
      removeErrorMessage: vi.fn(),
    });
    (useParams as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      conversationId: "test-id",
    });
    (useConfig as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      data: { APP_MODE: "local" },
    });
    (useGetTrajectory as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      mutate: vi.fn(),
      mutateAsync: vi.fn(),
      isLoading: false,
    });
    (useUploadFiles as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      mutateAsync: vi
        .fn()
        .mockResolvedValue({ skipped_files: [], uploaded_files: [] }),
      isLoading: false,
    });
  });

  // Helper function to render with QueryClientProvider
  const renderWithQueryClient = (ui: React.ReactElement) =>
    render(
      <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
    );

  test("should show chat suggestions when there are no events", () => {
    (useWsClient as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      send: vi.fn(),
      isLoadingMessages: false,
      parsedEvents: [],
    });

    renderWithQueryClient(<ChatInterface />);

    // Check if ChatSuggestions is rendered
    expect(screen.getByTestId("chat-suggestions")).toBeInTheDocument();
  });

  test("should show chat suggestions when there are only environment events", () => {
    const environmentEvent: OpenHandsAction = {
      id: 1,
      source: "environment",
      action: "system",
      args: {
        content: "source .openhands/setup.sh",
        tools: null,
        openhands_version: null,
        agent_class: null,
      },
      message: "Running setup script",
      timestamp: "2025-07-01T00:00:00Z",
    };

    (useWsClient as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      send: vi.fn(),
      isLoadingMessages: false,
      parsedEvents: [environmentEvent],
    });

    renderWithQueryClient(<ChatInterface />);

    // Check if ChatSuggestions is still rendered with environment events
    expect(screen.getByTestId("chat-suggestions")).toBeInTheDocument();
  });

  test("should hide chat suggestions when there is a user message", () => {
    const userEvent: OpenHandsAction = {
      id: 1,
      source: "user",
      action: "message",
      args: {
        content: "Hello",
        image_urls: [],
        file_urls: [],
      },
      message: "Hello",
      timestamp: "2025-07-01T00:00:00Z",
    };

    (useWsClient as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      send: vi.fn(),
      isLoadingMessages: false,
      parsedEvents: [userEvent],
    });

    renderWithQueryClient(<ChatInterface />);

    // Check if ChatSuggestions is not rendered with user events
    expect(screen.queryByTestId("chat-suggestions")).not.toBeInTheDocument();
  });

  test("should hide chat suggestions when there is an optimistic user message", () => {
    (
      useOptimisticUserMessage as unknown as ReturnType<typeof vi.fn>
    ).mockReturnValue({
      setOptimisticUserMessage: vi.fn(),
      getOptimisticUserMessage: vi.fn(() => "Optimistic message"),
    });

    renderWithQueryClient(<ChatInterface />);

    // Check if ChatSuggestions is not rendered with optimistic user message
    expect(screen.queryByTestId("chat-suggestions")).not.toBeInTheDocument();
  });
});
