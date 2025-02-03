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
});
