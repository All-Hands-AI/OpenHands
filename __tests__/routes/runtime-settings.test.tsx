import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import SettingsService from "#/api/settings-service/settings-service.api";
import { MOCK_DEFAULT_USER_SETTINGS } from "#/mocks/handlers";
import RuntimeSettingsScreen from "#/routes/runtime-settings";

describe("RuntimeSettingsScreen", () => {
  it("renders the runtime section of the conversation settings", async () => {
    vi.spyOn(SettingsService, "getSettings").mockResolvedValue(
      MOCK_DEFAULT_USER_SETTINGS,
    );
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    render(<RuntimeSettingsScreen />, {
      wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      ),
    });

    expect(
      await screen.findByTestId("sdk-settings-worktree_base"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("sdk-settings-container_memory"),
    ).toBeInTheDocument();
  });
});
