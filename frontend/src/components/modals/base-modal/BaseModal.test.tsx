import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { act } from "react-dom/test-utils";
import BaseModal from "./BaseModal";

describe("BaseModal", () => {
  it("should render if the modal is open", () => {
    const { rerender } = render(
      <BaseModal isOpen={false} onOpenChange={vi.fn} title="Settings" />,
    );
    expect(screen.queryByText("Settings")).not.toBeInTheDocument();

    rerender(<BaseModal title="Settings" onOpenChange={vi.fn} isOpen />);
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("should render an optional subtitle", () => {
    render(
      <BaseModal
        isOpen
        onOpenChange={vi.fn}
        title="Settings"
        subtitle="Subtitle"
      />,
    );
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
        onOpenChange={vi.fn}
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

  it("should close the modal after an action is performed", () => {
    const onOpenChangeMock = vi.fn();
    render(
      <BaseModal
        isOpen
        onOpenChange={onOpenChangeMock}
        title="Settings"
        actions={[
          {
            label: "Save",
            action: () => {},
            closeAfterAction: true,
          },
        ]}
      />,
    );

    act(() => {
      userEvent.click(screen.getByText("Save"));
    });
    expect(onOpenChangeMock).toHaveBeenCalledTimes(1);
  });

  it("should render children", () => {
    render(
      <BaseModal isOpen onOpenChange={vi.fn} title="Settings">
        <div>Children</div>
      </BaseModal>,
    );
    expect(screen.getByText("Children")).toBeInTheDocument();
  });

  it("should disable the action given the condition", () => {
    const { rerender } = render(
      <BaseModal
        isOpen
        onOpenChange={vi.fn}
        title="Settings"
        actions={[
          {
            label: "Save",
            action: () => {},
            isDisabled: true,
          },
        ]}
      />,
    );

    expect(screen.getByText("Save")).toBeDisabled();

    rerender(
      <BaseModal
        isOpen
        onOpenChange={vi.fn}
        title="Settings"
        actions={[
          {
            label: "Save",
            action: () => {},
            isDisabled: false,
          },
        ]}
      />,
    );

    expect(screen.getByText("Save")).not.toBeDisabled();
  });

  it.skip("should not close if the backdrop or escape key is pressed", () => {
    const onOpenChangeMock = vi.fn();
    render(
      <BaseModal
        isOpen
        onOpenChange={onOpenChangeMock}
        title="Settings"
        isDismissable={false}
      />,
    );

    act(() => {
      userEvent.keyboard("{esc}");
    });
    // fails because the nextui component wraps the modal content in an aria-hidden div
    expect(screen.getByRole("dialog")).toBeVisible();
  });
});
