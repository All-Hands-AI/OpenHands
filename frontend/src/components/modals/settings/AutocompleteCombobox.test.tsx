import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { vi } from "vitest";
import { AutocompleteCombobox } from "./AutocompleteCombobox";

const onChangeMock = vi.fn();

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
      tooltip="tooltip"
      onChange={onChangeMock}
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

  it("should call the onChange handler when a new value is selected", () => {
    renderComponent();

    const modelInput = screen.getByRole("combobox", { name: "model" });
    expect(modelInput).toHaveValue("model1");

    act(() => {
      userEvent.click(modelInput);
    });

    const model2 = screen.getByText("model2");
    act(() => {
      userEvent.click(model2);
    });

    expect(onChangeMock).toHaveBeenCalledWith("model2");
  });

  it("should set the input value to the default key if the default key is not in the list", () => {
    render(
      <AutocompleteCombobox
        ariaLabel="model"
        items={[{ value: "m1", label: "model1" }]}
        defaultKey="m2"
        tooltip="tooltip"
        onChange={onChangeMock}
      />,
    );

    const modelInput = screen.getByRole("combobox", { name: "model" });

    expect(modelInput).toHaveValue("m2");
  });

  it.todo("should show a tooltip after 0.5 seconds of focus");
});
