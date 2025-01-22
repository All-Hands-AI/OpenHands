import {
  EmbeddedCheckoutProvider,
  EmbeddedCheckout,
} from "@stripe/react-stripe-js";
import { loadStripe } from "@stripe/stripe-js";
import { TEST_STRIPE_PUBLIC_KEY } from "#/utils/stripe-test-keys";

const stripePromise = loadStripe(TEST_STRIPE_PUBLIC_KEY);

interface CheckoutFormProps {
  clientSecret: string;
}

export function StripeCheckoutForm({ clientSecret }: CheckoutFormProps) {
  return (
    <div data-testid="stripe-checkout-form">
      <EmbeddedCheckoutProvider
        stripe={stripePromise}
        options={{ clientSecret }}
      >
        <EmbeddedCheckout />
      </EmbeddedCheckoutProvider>
    </div>
  );
}
