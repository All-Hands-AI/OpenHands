import { render, screen, act } from "@testing-library/react";
import React from "react";
import userEvent from "@testing-library/user-event";
import { AutocompleteCombobox } from "./AutocompleteCombobox";

const renderComponent = () =>
  render(
    <AutocompleteCombobox
      ariaLabel="model"
      items={[
        { value: "m1", label: "model1" },
        { value: "m2", label: "model2" },
        { value: "m3", label: "model3" },
      ]}
      defaultKey="m1"
    />,
  );

describe("AutocompleteCombobox", () => {
  it("should render a combobox with the default value", () => {
    renderComponent();

    const modelInput = screen.getByRole("combobox", { name: "model" });
    expect(modelInput).toHaveValue("model1");
  });

  it("should open a dropdown with the available values", () => {
    renderComponent();

    const modelInput = screen.getByRole("combobox", { name: "model" });

    expect(screen.queryByText("model2")).not.toBeInTheDocument();
    expect(screen.queryByText("model3")).not.toBeInTheDocument();

    act(() => {
      userEvent.click(modelInput);
    });

    expect(screen.getByText("model2")).toBeInTheDocument();
    expect(screen.getByText("model3")).toBeInTheDocument();
  });
});
