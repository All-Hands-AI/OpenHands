import { http, HttpResponse } from "msw";
import Stripe from "stripe";
import { TEST_STRIPE_SECRET_KEY } from "#/utils/stripe-test-keys";

const PRICES: Record<number, string> = {
  "25": "price_1Qk3elK5Ces1YVhflhgIflrx",
  "50": "price_1Qk2qwK5Ces1YVhfSbLbgNYg",
  "100": "price_1Qk2mZK5Ces1YVhfu8XNJuxU",
};

export const STRIPE_BILLING_HANDLERS = [
  http.get("/api/credits", () => HttpResponse.json({ credits: 100 })),

  http.post("/api/create-checkout-session", async ({ request }) => {
    const body = await request.json();

    if (body && typeof body === "object" && body.amount) {
      const price = PRICES[body.amount];
      if (!price) {
        return HttpResponse.json(
          { message: "Invalid amount" },
          { status: 400 },
        );
      }

      const stripe = new Stripe(TEST_STRIPE_SECRET_KEY);
      const session = await stripe.checkout.sessions.create({
        ui_mode: "embedded",
        line_items: [
          {
            price,
            quantity: 1,
          },
        ],
        mode: "payment",
        payment_intent_data: {
          metadata: {
            // NOTE: This data will be sent on the server via cookie data
            user_id: "abc-123-test",
          },
        },
        return_url: `http://localhost:3001/billing?session_id={CHECKOUT_SESSION_ID}`,
      });

      return HttpResponse.json({ clientSecret: session.client_secret });
    }

    return HttpResponse.json({ message: "Invalid request" }, { status: 400 });
  }),

  http.get("/api/session-status", async ({ request }) => {
    const url = new URL(request.url);
    const sessionId = url.searchParams.get("session_id")?.toString();

    if (!sessionId) {
      return HttpResponse.json(
        { message: "Session not found" },
        { status: 404 },
      );
    }

    const stripe = new Stripe(TEST_STRIPE_SECRET_KEY);
    const session = await stripe.checkout.sessions.retrieve(sessionId);

    return HttpResponse.json({
      status: session.status,
      customer_email: session.customer_details?.email,
    });
  }),
];
