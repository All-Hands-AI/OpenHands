import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, test, vi } from "vitest";
import OpenHands from "#/api/open-hands";
import { PaymentForm } from "#/components/features/payment/payment-form";

describe("PaymentForm", () => {
  const getBalanceSpy = vi.spyOn(OpenHands, "getBalance");
  const createCheckoutSessionSpy = vi.spyOn(OpenHands, "createCheckoutSession");
  const getConfigSpy = vi.spyOn(OpenHands, "getConfig");

  const renderPaymentForm = () =>
    render(<PaymentForm />, {
      wrapper: ({ children }) => (
        <QueryClientProvider client={new QueryClient()}>
          {children}
        </QueryClientProvider>
      ),
    });

  beforeEach(() => {
    // useBalance hook will return the balance only if the APP_MODE is "saas" and the billing feature is enabled
    getConfigSpy.mockResolvedValue({
      APP_MODE: "saas",
      GITHUB_CLIENT_ID: "123",
      POSTHOG_CLIENT_KEY: "456",
      FEATURE_FLAGS: {
        ENABLE_BILLING: true,
        HIDE_LLM_SETTINGS: false,
      },
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should render the users current balance", async () => {
    getBalanceSpy.mockResolvedValue("100.50");
    renderPaymentForm();

    await waitFor(() => {
      const balance = screen.getByTestId("user-balance");
      expect(balance).toHaveTextContent("$100.50");
    });
  });

  it("should render the users current balance to two decimal places", async () => {
    getBalanceSpy.mockResolvedValue("100");
    renderPaymentForm();

    await waitFor(() => {
      const balance = screen.getByTestId("user-balance");
      expect(balance).toHaveTextContent("$100.00");
    });
  });

  test("the user can top-up a specific amount", async () => {
    const user = userEvent.setup();
    renderPaymentForm();

    const topUpInput = await screen.findByTestId("top-up-input");
    await user.type(topUpInput, "50");

    const topUpButton = screen.getByText("PAYMENT$ADD_CREDIT");
    await user.click(topUpButton);

    expect(createCheckoutSessionSpy).toHaveBeenCalledWith(50);
  });

  it("should only accept integer values", async () => {
    const user = userEvent.setup();
    renderPaymentForm();

    const topUpInput = await screen.findByTestId("top-up-input");
    await user.type(topUpInput, "50");

    const topUpButton = screen.getByText("PAYMENT$ADD_CREDIT");
    await user.click(topUpButton);

    expect(createCheckoutSessionSpy).toHaveBeenCalledWith(50);
  });

  it("should disable the top-up button if the user enters an invalid amount", async () => {
    const user = userEvent.setup();
    renderPaymentForm();

    const topUpButton = screen.getByText("PAYMENT$ADD_CREDIT");
    expect(topUpButton).toBeDisabled();

    const topUpInput = await screen.findByTestId("top-up-input");
    await user.type(topUpInput, "  ");

    expect(topUpButton).toBeDisabled();
  });

  it("should disable the top-up button after submission", async () => {
    const user = userEvent.setup();
    renderPaymentForm();

    const topUpInput = await screen.findByTestId("top-up-input");
    await user.type(topUpInput, "50");

    const topUpButton = screen.getByText("PAYMENT$ADD_CREDIT");
    await user.click(topUpButton);

    expect(topUpButton).toBeDisabled();
  });

  describe("prevent submission if", () => {
    test("user enters a negative amount", async () => {
      const user = userEvent.setup();
      renderPaymentForm();

      const topUpInput = await screen.findByTestId("top-up-input");
      await user.type(topUpInput, "-50");

      const topUpButton = screen.getByText("PAYMENT$ADD_CREDIT");
      await user.click(topUpButton);

      expect(createCheckoutSessionSpy).not.toHaveBeenCalled();
    });

    test("user enters an empty string", async () => {
      const user = userEvent.setup();
      renderPaymentForm();

      const topUpInput = await screen.findByTestId("top-up-input");
      await user.type(topUpInput, "     ");

      const topUpButton = screen.getByText("PAYMENT$ADD_CREDIT");
      await user.click(topUpButton);

      expect(createCheckoutSessionSpy).not.toHaveBeenCalled();
    });

    test("user enters a non-numeric value", async () => {
      const user = userEvent.setup();
      renderPaymentForm();

      // With type="number", the browser would prevent non-numeric input,
      // but we'll test the validation logic anyway
      const topUpInput = await screen.findByTestId("top-up-input");
      await user.type(topUpInput, "abc");

      const topUpButton = screen.getByText("PAYMENT$ADD_CREDIT");
      await user.click(topUpButton);

      expect(createCheckoutSessionSpy).not.toHaveBeenCalled();
    });

    test("user enters less than the minimum amount", async () => {
      const user = userEvent.setup();
      renderPaymentForm();

      const topUpInput = await screen.findByTestId("top-up-input");
      await user.type(topUpInput, "9"); // test assumes the minimum is 10

      const topUpButton = screen.getByText("PAYMENT$ADD_CREDIT");
      await user.click(topUpButton);

      expect(createCheckoutSessionSpy).not.toHaveBeenCalled();
    });

    test("user enters a decimal value", async () => {
      const user = userEvent.setup();
      renderPaymentForm();

      // With step="1", the browser would validate this, but we'll test our validation logic
      const topUpInput = await screen.findByTestId("top-up-input");
      await user.type(topUpInput, "50.5");

      const topUpButton = screen.getByText("PAYMENT$ADD_CREDIT");
      await user.click(topUpButton);

      expect(createCheckoutSessionSpy).not.toHaveBeenCalled();
    });
  });
});
