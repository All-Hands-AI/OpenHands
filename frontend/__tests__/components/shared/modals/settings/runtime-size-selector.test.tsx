import { screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { renderWithProviders } from "test-utils";
import { RuntimeSizeSelector } from "#/components/shared/modals/settings/runtime-size-selector";

const renderRuntimeSizeSelector = () =>
  renderWithProviders(<RuntimeSizeSelector isDisabled={false} />);

describe("RuntimeSizeSelector", () => {
  it("should show both runtime size options", () => {
    renderRuntimeSizeSelector();
    // The options are in the hidden select element
    const select = screen.getByRole("combobox", { hidden: true });
    expect(select).toHaveValue("1");
    expect(select).toHaveDisplayValue("1x (2 core, 8G)");
    expect(select.children).toHaveLength(3); // Empty option + 2 size options
  });

  it("should show the full description text for disabled options", async () => {
    renderRuntimeSizeSelector();

    // Click the button to open the dropdown
    const button = screen.getByRole("button", {
      name: "1x (2 core, 8G) SETTINGS_FORM$RUNTIME_SIZE_LABEL",
    });
    button.click();

    // Wait for the dropdown to open and find the description text
    const description = await screen.findByText(
      "Runtime sizes over 1 are disabled by default, please contact contact@all-hands.dev to get access to larger runtimes.",
    );
    expect(description).toBeInTheDocument();
    expect(description).toHaveClass("whitespace-normal", "break-words");
  });
});
