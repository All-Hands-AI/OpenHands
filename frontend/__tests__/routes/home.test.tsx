import { createRoutesStub } from "react-router";
import { describe, expect, it } from "vitest";
import { renderWithProviders } from "test-utils";
import userEvent from "@testing-library/user-event";
import { screen } from "@testing-library/react";
import MainApp from "#/routes/_oh/route";
import SettingsScreen from "#/routes/settings";

describe("Home Screen", () => {
  const RouterStub = createRoutesStub([
    {
      Component: MainApp,
      path: "/",
    },
    {
      Component: SettingsScreen,
      path: "/settings",
    },
  ]);

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
});
