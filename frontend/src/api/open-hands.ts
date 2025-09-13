import { openHands } from "./open-hands-axios";
import { SubscriptionAccess } from "#/types/billing";

class OpenHands {
  static async createCheckoutSession(amount: number): Promise<string> {
    const { data } = await openHands.post(
      "/api/billing/create-checkout-session",
      {
        amount,
      },
    );
    return data.redirect_url;
  }

  static async createBillingSessionResponse(): Promise<string> {
    const { data } = await openHands.post(
      "/api/billing/create-customer-setup-session",
    );
    return data.redirect_url;
  }

  static async getBalance(): Promise<string> {
    const { data } = await openHands.get<{ credits: string }>(
      "/api/billing/credits",
    );
    return data.credits;
  }

  static async getSubscriptionAccess(): Promise<SubscriptionAccess | null> {
    const { data } = await openHands.get<SubscriptionAccess | null>(
      "/api/billing/subscription-access",
    );
    return data;
  }
}

export default OpenHands;
