import React from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { AxiosError } from "axios";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AgentServerConversationService from "#/api/conversation-service/agent-server-conversation-service.api";
import { useCondenseConversation } from "#/hooks/mutation/use-condense-conversation";
import { createAgentServerQueryClient } from "#/query-client-config";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";

const { toastMock } = vi.hoisted(() => ({
  toastMock: Object.assign(vi.fn(), { success: vi.fn() }),
}));
vi.mock("react-hot-toast", () => ({ default: toastMock }));

/** The messages of every error toast shown, in order. */
const errorToastMessages = () =>
  toastMock.mock.calls.map(
    ([content]) =>
      (content as React.ReactElement<{ message: string }>).props.message,
  );

// The app's query client, so its global mutation error toast is in play too.
const createWrapper = () => {
  const client = createAgentServerQueryClient();
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client }, children);
  };
};

/** The shape the shared TypeScript client throws for a failed request. */
class HttpError extends Error {
  status: number;

  response: unknown;

  constructor(status: number, detail: string) {
    super(`HTTP request failed (${status}): ${JSON.stringify({ detail })}`);
    this.name = "HttpError";
    this.status = status;
    this.response = { detail };
  }
}

const NO_OP_DETAIL =
  "Cannot condense conversation: Condenser NoOpCondenser does not handle condensation requests";

describe("useCondenseConversation on failure", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    toastMock.mockClear();
  });

  it("leaves the error toast to its caller, so a refused compaction shows one toast", async () => {
    // Arrange
    vi.spyOn(
      AgentServerConversationService,
      "condenseConversation",
    ).mockRejectedValue(new HttpError(409, NO_OP_DETAIL));
    const { result } = renderHook(() => useCondenseConversation(), {
      wrapper: createWrapper(),
    });

    // Act: report the failure the way the Compact context action does.
    result.current.mutate(
      { conversationId: "c1", conversationUrl: null, sessionApiKey: null },
      {
        onError: (error) =>
          displayErrorToast(retrieveAxiosErrorMessage(error as AxiosError)),
      },
    );

    // Assert
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(errorToastMessages()).toEqual([NO_OP_DETAIL]);
  });
});
