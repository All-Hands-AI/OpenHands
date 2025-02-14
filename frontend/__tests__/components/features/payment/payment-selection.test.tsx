import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PaymentSelection } from "#/components/features/payment/payment-selection";

describe("PaymentSelection", () => {
  const onPaymentSelectionMock = vi.fn();

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render the top-up options", () => {
    const options = [25, 50, 100, 250];
    render(
      <PaymentSelection
        options={options}
        onPaymentSelection={onPaymentSelectionMock}
      />,
    );

    options.forEach((option) => {
      expect(screen.getByTestId(`option-${option}`)).toBeInTheDocument();
    });
  });

  it("should call the onPaymentSelection callback when a payment option is selected", async () => {
    const user = userEvent.setup();
    const options = [25, 50, 100, 250];
    render(
      <PaymentSelection
        options={options}
        onPaymentSelection={onPaymentSelectionMock}
      />,
    );

    await user.click(screen.getByTestId("option-50"));
    expect(onPaymentSelectionMock).toHaveBeenCalledWith(50);
  });
});
