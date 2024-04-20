import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { act } from "react-dom/test-utils";
import BaseModal from "./BaseModal";

describe("BaseModal", () => {
  it("should render if the modal is open", () => {
    const { rerender } = render(<BaseModal isOpen={false} title="Settings" />);
    expect(screen.queryByText("Settings")).not.toBeInTheDocument();

    rerender(<BaseModal title="Settings" isOpen />);
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("should not render the default close button", () => {
    render(<BaseModal isOpen title="Settings" />);
    expect(
      screen.queryByRole("button", { name: "Close" }),
    ).not.toBeInTheDocument();
  });

  it("should render an optional subtitle", () => {
    render(<BaseModal isOpen title="Settings" subtitle="Subtitle" />);
    expect(screen.getByText("Subtitle")).toBeInTheDocument();
  });

  it("should render actions", () => {
    const onPrimaryClickMock = vi.fn();
    const onSecondaryClickMock = vi.fn();

    const primaryAction = {
      action: onPrimaryClickMock,
      label: "Save",
    };

    const secondaryAction = {
      action: onSecondaryClickMock,
      label: "Cancel",
    };

    render(
      <BaseModal
        isOpen
        title="Settings"
        actions={[primaryAction, secondaryAction]}
      />,
    );

    expect(screen.getByText("Save")).toBeInTheDocument();
    expect(screen.getByText("Cancel")).toBeInTheDocument();

    act(() => {
      userEvent.click(screen.getByText("Save"));
    });
    expect(onPrimaryClickMock).toHaveBeenCalledTimes(1);

    act(() => {
      userEvent.click(screen.getByText("Cancel"));
    });
    expect(onSecondaryClickMock).toHaveBeenCalledTimes(1);
  });

  it("should render children", () => {
    render(
      <BaseModal isOpen title="Settings">
        <div>Children</div>
      </BaseModal>,
    );
    expect(screen.getByText("Children")).toBeInTheDocument();
  });
});
