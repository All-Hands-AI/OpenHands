import {
  EmbeddedCheckoutProvider,
  EmbeddedCheckout,
} from "@stripe/react-stripe-js";
import { loadStripe } from "@stripe/stripe-js";

const stripePromise = loadStripe("");

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
