import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { TOSModal } from "#/components/features/tos/tos-modal";
import * as SettingsContext from "#/context/settings-context";

vi.mock("#/context/settings-context", () => ({
  useCurrentSettings: vi.fn(),
}));

describe("TOSModal", () => {
  const saveUserSettingsSpy = vi.fn();
  const useCurrentSettingsSpy = vi.spyOn(SettingsContext, "useCurrentSettings");

  beforeEach(() => {
    useCurrentSettingsSpy.mockReturnValue({
      saveUserSettings: saveUserSettingsSpy,
      settings: undefined,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render the TOS modal", () => {
    render(<TOSModal />);

    expect(screen.getByTestId("tos-modal")).toBeInTheDocument();
    expect(screen.getByText("TOS$TITLE")).toBeInTheDocument();
    expect(screen.getByText("TOS$DESCRIPTION")).toBeInTheDocument();
    expect(screen.getByText("TOS$READ_MORE")).toBeInTheDocument();
    expect(screen.getByText("TOS$ACCEPT")).toBeInTheDocument();
  });

  it("should save settings when accepting TOS", async () => {
    const user = userEvent.setup();
    render(<TOSModal />);

    const acceptButton = screen.getByTestId("accept-tos-button");
    await user.click(acceptButton);

    expect(saveUserSettingsSpy).toHaveBeenCalledWith({ ACCEPT_TOS: true });
  });
});