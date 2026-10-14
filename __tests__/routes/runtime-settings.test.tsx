import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import SettingsService from "#/api/settings-service/settings-service.api";
import * as conversationWorkspace from "#/hooks/query/use-conversation-workspace";
import { MOCK_DEFAULT_USER_SETTINGS } from "#/mocks/handlers";
import RuntimeSettingsScreen from "#/routes/runtime-settings";

function renderRuntimeSettingsScreen({
  isolated = false,
  dockerSelectable = false,
}: { isolated?: boolean; dockerSelectable?: boolean } = {}) {
  vi.spyOn(conversationWorkspace, "useConversationWorkspace").mockReturnValue({
    isolated,
    dockerSelectable,
    unsupportedMessage: null,
  });
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(<RuntimeSettingsScreen />, {
    wrapper: ({ children }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    ),
  });
}

beforeEach(() => {
  vi.restoreAllMocks();
  vi.spyOn(SettingsService, "getSettings").mockResolvedValue(
    MOCK_DEFAULT_USER_SETTINGS,
  );
});

describe("RuntimeSettingsScreen", () => {
  it("offers only the worktree option when the server cannot run Docker", async () => {
    renderRuntimeSettingsScreen();

    expect(
      await screen.findByTestId("sdk-settings-worktree_base"),
    ).toBeInTheDocument();
    expect(
      screen.queryByTestId("sdk-settings-container_memory"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("sdk-settings-container_browser"),
    ).not.toBeInTheDocument();
  });

  it.each([
    ["selectable", { dockerSelectable: true }],
    ["Docker-only", { isolated: true }],
  ])(
    "offers the container options on a %s Docker server",
    async (_label, docker) => {
      renderRuntimeSettingsScreen(docker);

      expect(
        await screen.findByTestId("sdk-settings-worktree_base"),
      ).toBeInTheDocument();
      expect(
        screen.getByTestId("sdk-settings-container_browser"),
      ).toBeInTheDocument();
    },
  );
});
