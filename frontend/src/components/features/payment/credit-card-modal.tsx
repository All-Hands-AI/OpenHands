import { Elements } from "@stripe/react-stripe-js";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { useStripePromise } from "#/context/stripe-promise-context";
import { CreditCardForm } from "./credit-card-form";

export function CreditCardModal() {
  const stripePromise = useStripePromise();

  return (
    <ModalBackdrop>
      <Elements
        stripe={stripePromise}
        options={{
          mode: "setup",
          currency: "usd",
          appearance: {
            theme: "night",
            variables: {
              colorPrimary: "#C9B974",
              iconColor: "#C9B974",
            },
          },
        }}
      >
        <CreditCardForm />
      </Elements>
    </ModalBackdrop>
  );
}
