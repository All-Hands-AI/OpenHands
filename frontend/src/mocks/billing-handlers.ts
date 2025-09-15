import { delay, http, HttpResponse } from "msw";
import { SubscriptionAccess } from "#/types/billing";

// Mock data for different subscription scenarios
const MOCK_ACTIVE_SUBSCRIPTION: SubscriptionAccess = {
  start_at: "2024-01-01T00:00:00Z",
  end_at: "2024-12-31T23:59:59Z",
  created_at: "2024-01-01T00:00:00Z",
  cancelled_at: null,
  stripe_subscription_id: "sub_mock123456789",
};

const MOCK_CANCELLED_SUBSCRIPTION: SubscriptionAccess = {
  start_at: "2024-01-01T00:00:00Z",
  end_at: "2025-01-01T23:59:59Z",
  created_at: "2024-01-01T00:00:00Z",
  cancelled_at: "2024-06-15T10:30:00Z",
  stripe_subscription_id: "sub_mock123456789",
};

// Factory function to create billing handlers with different subscription states
function createBillingHandlers(subscriptionData: SubscriptionAccess | null) {
  return [
    http.get("/api/billing/credits", async () => {
      await delay();
      return HttpResponse.json({ credits: "100" });
    }),

    http.get("/api/billing/subscription-access", async () => {
      await delay();
      return HttpResponse.json(subscriptionData);
    }),

    http.post("/api/billing/create-checkout-session", async () => {
      await delay();
      return HttpResponse.json({
        redirect_url: "https://stripe.com/some-checkout",
      });
    }),

    http.post("/api/billing/subscription-checkout-session", async () => {
      await delay();
      return HttpResponse.json({
        redirect_url: "https://stripe.com/some-subscription-checkout",
      });
    }),

    http.post("/api/billing/create-customer-setup-session", async () => {
      await delay();
      return HttpResponse.json({
        redirect_url: "https://stripe.com/some-customer-setup",
      });
    }),

    http.post("/api/billing/cancel-subscription", async () => {
      await delay();
      return HttpResponse.json({
        status: "success",
        message: "Subscription cancelled successfully",
      });
    }),
  ];
}

// Export different handler sets for different testing scenarios
export const STRIPE_BILLING_HANDLERS = createBillingHandlers(
  MOCK_ACTIVE_SUBSCRIPTION,
);
export const STRIPE_BILLING_HANDLERS_NO_SUBSCRIPTION =
  createBillingHandlers(null);
export const STRIPE_BILLING_HANDLERS_CANCELLED_SUBSCRIPTION =
  createBillingHandlers(MOCK_CANCELLED_SUBSCRIPTION);
