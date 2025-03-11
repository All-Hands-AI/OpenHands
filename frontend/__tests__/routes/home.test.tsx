import { createRoutesStub } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "test-utils";
import userEvent from "@testing-library/user-event";
import { screen } from "@testing-library/react";
import { AxiosError } from "axios";
import MainApp from "#/routes/_oh/route";
import SettingsScreen from "#/routes/settings";
import Home from "#/routes/_oh._index/route";
import OpenHands from "#/api/open-hands";
import * as FeatureFlags from "#/utils/feature-flags";

const createAxiosNotFoundErrorObject = () =>
  new AxiosError(
    "Request failed with status code 404",
    "ERR_BAD_REQUEST",
    undefined,
    undefined,
    {
      status: 404,
      statusText: "Not Found",
      data: { message: "Settings not found" },
      headers: {},
      // @ts-expect-error - we only need the response object for this test
      config: {},
    },
  );

describe("Home Screen", () => {
  const getSettingsSpy = vi.spyOn(OpenHands, "getSettings");
  const getConfigSpy = vi.spyOn(OpenHands, "getConfig");

  const RouterStub = createRoutesStub([
    {
      // layout route
      Component: MainApp,
      path: "/",
      children: [
        {
          // home route
          Component: Home,
          path: "/",
        },
        {
          Component: SettingsScreen,
          path: "/settings",
        },
      ],
    },
  ]);

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render the home screen", () => {
    renderWithProviders(<RouterStub initialEntries={["/"]} />);
  });

  it("should navigate to the settings screen when the settings button is clicked", async () => {
    const user = userEvent.setup();
    renderWithProviders(<RouterStub initialEntries={["/"]} />);

    const settingsButton = await screen.findByTestId("settings-button");
    await user.click(settingsButton);

    const settingsScreen = await screen.findByTestId("settings-screen");
    expect(settingsScreen).toBeInTheDocument();
  });

  it("should navigate to the settings when pressing 'Connect to GitHub' if the user isn't authenticated", async () => {
    const user = userEvent.setup();
    renderWithProviders(<RouterStub initialEntries={["/"]} />);

    const connectToGitHubButton =
      await screen.findByTestId("connect-to-github");
    await user.click(connectToGitHubButton);

    const settingsScreen = await screen.findByTestId("settings-screen");
    expect(settingsScreen).toBeInTheDocument();
  });

  describe("Settings 404", () => {
    it("should open the settings modal if GET /settings fails with a 404", async () => {
      const error = createAxiosNotFoundErrorObject();
      getSettingsSpy.mockRejectedValue(error);

      renderWithProviders(<RouterStub initialEntries={["/"]} />);

      const settingsModal = await screen.findByTestId("ai-config-modal");
      expect(settingsModal).toBeInTheDocument();
    });

    it("should navigate to the settings screen when clicking the advanced settings button", async () => {
      const error = createAxiosNotFoundErrorObject();
      getSettingsSpy.mockRejectedValue(error);

      const user = userEvent.setup();
      renderWithProviders(<RouterStub initialEntries={["/"]} />);

      const settingsScreen = screen.queryByTestId("settings-screen");
      expect(settingsScreen).not.toBeInTheDocument();

      const settingsModal = await screen.findByTestId("ai-config-modal");
      expect(settingsModal).toBeInTheDocument();

      const advancedSettingsButton = await screen.findByTestId(
        "advanced-settings-link",
      );
      await user.click(advancedSettingsButton);

      const settingsScreenAfter = await screen.findByTestId("settings-screen");
      expect(settingsScreenAfter).toBeInTheDocument();

      const settingsModalAfter = screen.queryByTestId("ai-config-modal");
      expect(settingsModalAfter).not.toBeInTheDocument();
    });

    it("should not open the settings modal if GET /settings fails but is SaaS mode", async () => {
      // TODO: Remove HIDE_LLM_SETTINGS check once released
      vi.spyOn(FeatureFlags, "HIDE_LLM_SETTINGS").mockReturnValue(true);
      // @ts-expect-error - we only need APP_MODE for this test
      getConfigSpy.mockResolvedValue({ APP_MODE: "saas" });
      const error = createAxiosNotFoundErrorObject();
      getSettingsSpy.mockRejectedValue(error);

      renderWithProviders(<RouterStub initialEntries={["/"]} />);

      // small hack to wait for the modal to not appear
      await expect(
        screen.findByTestId("ai-config-modal", {}, { timeout: 1000 }),
      ).rejects.toThrow();
    });
  });
});
