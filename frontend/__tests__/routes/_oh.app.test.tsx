import { createRoutesStub } from "react-router";
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "test-utils";
import { screen, waitFor } from "@testing-library/react";
import App from "#/routes/conversation";
import OpenHands from "#/api/open-hands";
import * as CustomToast from "#/utils/custom-toast-handlers";

describe("App", () => {
  const errorToastSpy = vi.spyOn(CustomToast, "displayErrorToast");

  const RouteStub = createRoutesStub([
    { Component: App, path: "/conversation/:conversationId" },
  ]);

  beforeAll(() => {
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
});
