import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import SettingsService from "#/api/settings-service/settings-service.api";
import { MOCK_DEFAULT_USER_SETTINGS } from "#/mocks/handlers";
import RuntimeSettingsScreen from "#/routes/runtime-settings";

const RUNTIME_OPTION_IDS = [
  "sdk-settings-worktree_base",
  "sdk-settings-container_memory",
  "sdk-settings-container_cpus",
  "sdk-settings-container_browser",
];

async function renderWithDefaultRuntime(defaultRuntime: string) {
  vi.spyOn(SettingsService, "getSettings").mockResolvedValue({
    ...MOCK_DEFAULT_USER_SETTINGS,
    conversation_settings: { default_runtime: defaultRuntime },
  });
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(<RuntimeSettingsScreen />, {
    wrapper: ({ children }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    ),
  });
  await screen.findByTestId("sdk-settings-default_runtime");
  return RUNTIME_OPTION_IDS.filter((id) => screen.queryByTestId(id));
}

describe("RuntimeSettingsScreen", () => {
  it.each([
    ["local", []],
    ["worktree", ["sdk-settings-worktree_base"]],
    [
      "docker",
      [
        "sdk-settings-container_memory",
        "sdk-settings-container_cpus",
        "sdk-settings-container_browser",
      ],
    ],
  ])("shows only the %s runtime's options", async (runtime, expected) => {
    expect(await renderWithDefaultRuntime(runtime)).toEqual(expected);
  });
});
