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
        ENABLE_JIRA: false,
        ENABLE_JIRA_DC: false,
        ENABLE_LINEAR: false,
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

  describe("Cancel Subscription", () => {
    const getSubscriptionAccessSpy = vi.spyOn(
      OpenHands,
      "getSubscriptionAccess",
    );
    const cancelSubscriptionSpy = vi.spyOn(OpenHands, "cancelSubscription");

    beforeEach(() => {
      // Mock active subscription
      getSubscriptionAccessSpy.mockResolvedValue({
        start_at: "2024-01-01T00:00:00Z",
        end_at: "2024-12-31T23:59:59Z",
        created_at: "2024-01-01T00:00:00Z",
      });
    });

    it("should render cancel subscription button when user has active subscription", async () => {
      renderPaymentForm();

      await waitFor(() => {
        const cancelButton = screen.getByTestId("cancel-subscription-button");
        expect(cancelButton).toBeInTheDocument();
        expect(cancelButton).toHaveTextContent("PAYMENT$CANCEL_SUBSCRIPTION");
      });
    });

    it("should not render cancel subscription button when user has no subscription", async () => {
      getSubscriptionAccessSpy.mockResolvedValue(null);
      renderPaymentForm();

      await waitFor(() => {
        const cancelButton = screen.queryByTestId("cancel-subscription-button");
        expect(cancelButton).not.toBeInTheDocument();
      });
    });

    it("should show confirmation modal when cancel subscription button is clicked", async () => {
      const user = userEvent.setup();
      renderPaymentForm();

      const cancelButton = await screen.findByTestId(
        "cancel-subscription-button",
      );
      await user.click(cancelButton);

      // Should show confirmation modal
      expect(
        screen.getByTestId("cancel-subscription-modal"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("PAYMENT$CANCEL_SUBSCRIPTION_TITLE"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("PAYMENT$CANCEL_SUBSCRIPTION_MESSAGE"),
      ).toBeInTheDocument();
      expect(screen.getByTestId("confirm-cancel-button")).toBeInTheDocument();
      expect(screen.getByTestId("modal-cancel-button")).toBeInTheDocument();
    });

    it("should close modal when cancel button in modal is clicked", async () => {
      const user = userEvent.setup();
      renderPaymentForm();

      const cancelButton = await screen.findByTestId(
        "cancel-subscription-button",
      );
      await user.click(cancelButton);

      // Modal should be visible
      expect(
        screen.getByTestId("cancel-subscription-modal"),
      ).toBeInTheDocument();

      // Click cancel in modal
      const modalCancelButton = screen.getByTestId("modal-cancel-button");
      await user.click(modalCancelButton);

      // Modal should be closed
      expect(
        screen.queryByTestId("cancel-subscription-modal"),
      ).not.toBeInTheDocument();
    });

    it("should call cancel subscription API when confirm button is clicked", async () => {
      const user = userEvent.setup();
      renderPaymentForm();

      const cancelButton = await screen.findByTestId(
        "cancel-subscription-button",
      );
      await user.click(cancelButton);

      // Click confirm in modal
      const confirmButton = screen.getByTestId("confirm-cancel-button");
      await user.click(confirmButton);

      // Should call the cancel subscription API
      expect(cancelSubscriptionSpy).toHaveBeenCalled();
    });

    it("should close modal after successful cancellation", async () => {
      const user = userEvent.setup();
      cancelSubscriptionSpy.mockResolvedValue({
        status: "success",
        message: "Subscription cancelled successfully",
      });
      renderPaymentForm();

      const cancelButton = await screen.findByTestId(
        "cancel-subscription-button",
      );
      await user.click(cancelButton);

      const confirmButton = screen.getByTestId("confirm-cancel-button");
      await user.click(confirmButton);

      // Wait for API call to complete and modal to close
      await waitFor(() => {
        expect(
          screen.queryByTestId("cancel-subscription-modal"),
        ).not.toBeInTheDocument();
      });
    });
  });
});
