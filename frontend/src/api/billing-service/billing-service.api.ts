import { openHands } from "../open-hands-axios";
import {
  CancelSubscriptionResponse,
  SubscriptionAccess,
} from "./billing.types";

/**
 * Billing Service API - Handles all billing-related API endpoints
 */
class BillingService {
  /**
   * Create a Stripe checkout session for credit purchase
   * @param amount The amount to charge in dollars
   * @returns The redirect URL for the checkout session
   */
  static async createCheckoutSession(amount: number): Promise<string> {
    const { data } = await openHands.post(
      "/api/billing/create-checkout-session",
      {
        amount,
      },
    );
    return data.redirect_url;
  }

  /**
   * Create a customer setup session for payment method management
   * @returns The redirect URL for the customer setup session
   */
  static async createBillingSessionResponse(): Promise<string> {
    const { data } = await openHands.post(
      "/api/billing/create-customer-setup-session",
    );
    return data.redirect_url;
  }

  /**
   * Get the user's current credit balance
   * @returns The user's credit balance as a string
   */
  static async getBalance(): Promise<string> {
    const { data } = await openHands.get<{ credits: string }>(
      "/api/billing/credits",
    );
    return data.credits;
  }

  /**
   * Get the user's subscription access information
   * @returns The user's subscription access details or null if not available
   */
  static async getSubscriptionAccess(): Promise<SubscriptionAccess | null> {
    const { data } = await openHands.get<SubscriptionAccess | null>(
      "/api/billing/subscription-access",
    );
    return data;
  }

  /**
   * Create a subscription checkout session for subscribing to a plan
   * @returns The redirect URL for the subscription checkout session
   */
  static async createSubscriptionCheckoutSession(): Promise<{
    redirect_url?: string;
  }> {
    const { data } = await openHands.post(
      "/api/billing/subscription-checkout-session",
    );
    return data;
  }

  /**
   * Cancel the user's subscription
   * @returns The response indicating the result of the cancellation request
   */
  static async cancelSubscription(): Promise<CancelSubscriptionResponse> {
    const { data } = await openHands.post<CancelSubscriptionResponse>(
      "/api/billing/cancel-subscription",
    );
    return data;
  }
}

export default BillingService;
