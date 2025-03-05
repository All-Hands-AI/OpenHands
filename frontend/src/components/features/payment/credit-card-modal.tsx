import React from "react";
import { Elements } from "@stripe/react-stripe-js";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { useStripePromise } from "#/context/stripe-promise-context";
import { CreditCardForm } from "./credit-card-form";
import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";


export const CreditCardModal = () => {
  const stripePromise = useStripePromise();
  const { data: clientSecret, isFetching } = useQuery({
      queryKey: ["createSetupIntent"],
      queryFn: OpenHands.createSetupIntent,
    });

  if (isFetching) {
    return null;
  }

  return (
    <ModalBackdrop>
        <Elements
            stripe={stripePromise}
            options={{
              //mode: "setup",
              currency: "usd",
              appearance: {
                theme: "night",
                variables: {
                  colorPrimary: "#C9B974",
                  iconColor: "#C9B974",
                },
              },
              clientSecret: clientSecret as any,
            }}
          >
          <CreditCardForm />
        </Elements>
    </ModalBackdrop>
  );
};
