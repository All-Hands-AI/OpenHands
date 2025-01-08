import { createRoutesStub } from "react-router";
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "test-utils";
import { screen, waitFor } from "@testing-library/react";
import toast from "react-hot-toast";
import App from "#/routes/_oh.app/route";
import OpenHands from "#/api/open-hands";
import { MULTI_CONVERSATION_UI } from "#/utils/feature-flags";

describe("App", () => {
  const RouteStub = createRoutesStub([
    { Component: App, path: "/conversation/:conversationId" },
  ]);

  const { endSessionMock } = vi.hoisted(() => ({
    endSessionMock: vi.fn(),
  }));

  beforeAll(() => {
    vi.mock("#/hooks/use-end-session", () => ({
      useEndSession: vi.fn(() => endSessionMock),
    }));

    vi.mock("#/hooks/use-terminal", () => ({
      useTerminal: vi.fn(),
    }));
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render", async () => {
    renderWithProviders(<RouteStub initialEntries={["/conversation/123"]} />);
    await screen.findByTestId("app-route");
  });

  it.skipIf(!MULTI_CONVERSATION_UI)(
    "should call endSession if the user does not have permission to view conversation",
    async () => {
      const errorToastSpy = vi.spyOn(toast, "error");
      const getConversationSpy = vi.spyOn(OpenHands, "getConversation");

      getConversationSpy.mockResolvedValue(null);
      renderWithProviders(
        <RouteStub initialEntries={["/conversation/9999"]} />,
      );

      await waitFor(() => {
        expect(endSessionMock).toHaveBeenCalledOnce();
        expect(errorToastSpy).toHaveBeenCalledOnce();
      });
    },
  );

  it("should not call endSession if the user has permission", async () => {
    const errorToastSpy = vi.spyOn(toast, "error");
    const getConversationSpy = vi.spyOn(OpenHands, "getConversation");

    getConversationSpy.mockResolvedValue({
      conversation_id: "9999",
      last_updated_at: "",
      created_at: "",
      title: "",
      selected_repository: "",
      status: "STOPPED",
    });
    const { rerender } = renderWithProviders(
      <RouteStub initialEntries={["/conversation/9999"]} />,
    );

    await waitFor(() => {
      expect(endSessionMock).not.toHaveBeenCalled();
      expect(errorToastSpy).not.toHaveBeenCalled();
    });

    rerender(<RouteStub initialEntries={["/conversation"]} />);

    await waitFor(() => {
      expect(endSessionMock).not.toHaveBeenCalled();
      expect(errorToastSpy).not.toHaveBeenCalled();
    });
  });
});
