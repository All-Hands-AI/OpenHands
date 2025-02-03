import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SettingsSwitch } from "#/components/features/settings/settings-switch";

describe("SettingsSwitch", () => {
  it("should call the onChange handler when the input is clicked", async () => {
    const user = userEvent.setup();
    const onToggleMock = vi.fn();
    render(
      <SettingsSwitch testId="test-switch" onToggle={onToggleMock}>
        Test Switch
      </SettingsSwitch>,
    );

    const switchInput = screen.getByTestId("test-switch");

    await user.click(switchInput);
    expect(onToggleMock).toHaveBeenCalledWith(true);

    await user.click(switchInput);
    expect(onToggleMock).toHaveBeenCalledWith(false);
  });

  it("should render an optional tag if showOptionalTag is true", () => {
    const { rerender } = render(
      <SettingsSwitch testId="test-switch">Test Switch</SettingsSwitch>,
    );

    expect(screen.queryByText(/optional/i)).not.toBeInTheDocument();

    rerender(
      <SettingsSwitch testId="test-switch" showOptionalTag>
        Test Switch
      </SettingsSwitch>,
    );

    expect(screen.getByText(/optional/i)).toBeInTheDocument();
  });

  it("should be able to set a default toggle state", async () => {
    const user = userEvent.setup();
    const onToggleMock = vi.fn();
    render(
      <SettingsSwitch
        testId="test-switch"
        onToggle={onToggleMock}
        defaultIsToggled
      >
        Test Switch
      </SettingsSwitch>,
    );

    expect(screen.getByTestId("test-switch")).toBeChecked();

    const switchInput = screen.getByTestId("test-switch");
    await user.click(switchInput);
    expect(onToggleMock).toHaveBeenCalledWith(false);

    expect(screen.getByTestId("test-switch")).not.toBeChecked();
  });
});
