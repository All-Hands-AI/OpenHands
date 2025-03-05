import React from "react";
import { Elements } from "@stripe/react-stripe-js";
import { useQuery } from "@tanstack/react-query";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { useStripePromise } from "#/context/stripe-promise-context";
import { CreditCardForm } from "./credit-card-form";
import OpenHands from "#/api/open-hands";

export function CreditCardModal() {
  const stripePromise = useStripePromise();
  const { data: customerSession, isFetching } = useQuery({
    queryKey: ["createSetupIntent"],
    queryFn: OpenHands.createCustomerSetupSession,
  });

  if (isFetching) {
    return null;
  }

  return (
    <ModalBackdrop>
      <Elements
        stripe={stripePromise}
        options={{
          // mode: "setup",
          currency: "usd",
          appearance: {
            theme: "night",
            variables: {
              colorPrimary: "#C9B974",
              iconColor: "#C9B974",
            },
          },
          clientSecret: customerSession?.client_secret,
        }}
      >
        <CreditCardForm />
      </Elements>
    </ModalBackdrop>
  );
}
