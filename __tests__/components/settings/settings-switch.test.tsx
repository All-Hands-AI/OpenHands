/* eslint-disable i18next/no-literal-string -- test fixtures use literal labels */
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

  it("should render a beta tag if isBeta is true", () => {
    const { rerender } = render(
      <SettingsSwitch testId="test-switch" onToggle={vi.fn()} isBeta={false}>
        Test Switch
      </SettingsSwitch>,
    );

    expect(screen.queryByText(/beta/i)).not.toBeInTheDocument();

    rerender(
      <SettingsSwitch testId="test-switch" onToggle={vi.fn()} isBeta>
        Test Switch
      </SettingsSwitch>,
    );

    expect(screen.getByText(/beta/i)).toBeInTheDocument();
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

  it("is exposed as an accessible checkbox with its label as accessible name", () => {
    render(
      <SettingsSwitch testId="test-switch" onToggle={vi.fn()}>
        Sound Notifications
      </SettingsSwitch>,
    );

    const checkbox = screen.getByRole("checkbox", {
      name: "Sound Notifications",
    });
    expect(checkbox).toBeInTheDocument();
    expect(checkbox).not.toBeChecked();
  });

  it("can be focused with Tab and toggled with Space", async () => {
    const user = userEvent.setup();
    const onToggleMock = vi.fn();
    render(
      <>
        <button type="button">Before</button>
        <SettingsSwitch testId="test-switch" onToggle={onToggleMock}>
          Send anonymous usage data
        </SettingsSwitch>
      </>,
    );

    const button = screen.getByRole("button", { name: "Before" });
    button.focus();
    expect(button).toHaveFocus();

    await user.tab();
    const checkbox = screen.getByRole("checkbox", {
      name: "Send anonymous usage data",
    });
    expect(checkbox).toHaveFocus();

    await user.keyboard(" ");
    expect(onToggleMock).toHaveBeenCalledWith(true);

    await user.keyboard(" ");
    expect(onToggleMock).toHaveBeenCalledWith(false);
  });

  it("cannot be focused or toggled when disabled", async () => {
    const user = userEvent.setup();
    const onToggleMock = vi.fn();
    render(
      <>
        <button type="button">Before</button>
        <SettingsSwitch testId="test-switch" onToggle={onToggleMock} isDisabled>
          Disabled Switch
        </SettingsSwitch>
      </>,
    );

    const button = screen.getByRole("button", { name: "Before" });
    button.focus();
    await user.tab();

    const checkbox = screen.getByRole("checkbox", {
      name: "Disabled Switch",
    });
    expect(checkbox).not.toHaveFocus();
    expect(checkbox).toBeDisabled();

    await user.click(checkbox);
    expect(onToggleMock).not.toHaveBeenCalled();
  });
});
