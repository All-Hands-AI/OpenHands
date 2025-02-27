import { delay, http, HttpResponse } from "msw";
import Stripe from "stripe";

const TEST_STRIPE_SECRET_KEY = "";
const PRICE_ID = "";

export const STRIPE_BILLING_HANDLERS = [
  http.get("/api/billing/credits", async () => {
    await delay();
    return HttpResponse.json({ credits: "100" });
  }),

  http.post("/api/billing/create-checkout-session", async ({ request }) => {
    await delay();
    const body = await request.json();

    if (body && typeof body === "object" && body.amount) {
      const stripe = new Stripe(TEST_STRIPE_SECRET_KEY);
      const session = await stripe.checkout.sessions.create({
        line_items: [
          {
            price: PRICE_ID,
            quantity: body.amount,
          },
        ],
        mode: "payment",
        success_url: "http://localhost:3001/settings/billing/?checkout=success",
        cancel_url: "http://localhost:3001/settings/billing/?checkout=cancel",
      });

      if (session.url) return HttpResponse.json({ redirect_url: session.url });
    }

    return HttpResponse.json({ message: "Invalid request" }, { status: 400 });
  }),
];
