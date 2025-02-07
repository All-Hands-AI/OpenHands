import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SettingsInput } from "#/components/features/settings/settings-input";

describe("SettingsInput", () => {
  it("should render an optional tag if showOptionalTag is true", async () => {
    const { rerender } = render(
      <SettingsInput testId="test-input" label="Test Input" type="text" />,
    );

    expect(screen.queryByText(/optional/i)).not.toBeInTheDocument();

    rerender(
      <SettingsInput
        testId="test-input"
        showOptionalTag
        label="Test Input"
        type="text"
      />,
    );

    expect(screen.getByText(/optional/i)).toBeInTheDocument();
  });

  it("should disable the input if isDisabled is true", async () => {
    const { rerender } = render(
      <SettingsInput testId="test-input" label="Test Input" type="text" />,
    );

    expect(screen.getByTestId("test-input")).toBeEnabled();

    rerender(
      <SettingsInput
        testId="test-input"
        label="Test Input"
        type="text"
        isDisabled
      />,
    );

    expect(screen.getByTestId("test-input")).toBeDisabled();
  });

  it("should set a placeholder on the input", async () => {
    render(
      <SettingsInput
        testId="test-input"
        label="Test Input"
        type="text"
        placeholder="Test Placeholder"
      />,
    );

    expect(screen.getByTestId("test-input")).toHaveAttribute(
      "placeholder",
      "Test Placeholder",
    );
  });

  it("should set a default value on the input", async () => {
    render(
      <SettingsInput
        testId="test-input"
        label="Test Input"
        type="text"
        defaultValue="Test Value"
      />,
    );

    expect(screen.getByTestId("test-input")).toHaveValue("Test Value");
  });

  it("should render a badge if content is provided", async () => {
    const { rerender } = render(
      <SettingsInput testId="test-input" label="Test Input" type="text" />,
    );

    expect(screen.queryByTestId("badge")).not.toBeInTheDocument();

    rerender(
      <SettingsInput
        testId="test-input"
        label="Test Input"
        type="text"
        badgeContent="Test Badge"
      />,
    );

    const badge = screen.getByTestId("badge");

    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent("Test Badge");
  });
});
