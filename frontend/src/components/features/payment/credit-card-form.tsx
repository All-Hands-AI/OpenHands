import React from "react";
import {
  PaymentElement,
  useElements,
  useStripe,
} from "@stripe/react-stripe-js";
import { StripePaymentElementChangeEvent } from "@stripe/stripe-js";
import { useMutation } from "@tanstack/react-query";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { BrandButton } from "../settings/brand-button";
import OpenHands from "#/api/open-hands";

export function CreditCardForm() {
  const [formComplete, setFormComplete] = React.useState(false);
  const [paymentFormErrorMessage, setPaymentFormErrorMessage] =
    React.useState("");
  const stripe = useStripe();
  const elements = useElements();

  const { mutateAsync: createIntent } = useMutation({
    mutationKey: ["createSetupIntent"],
    mutationFn: OpenHands.createCustomerSetupSession,
  });

  const formAction = async () => {
    setPaymentFormErrorMessage("");

    if (!stripe || !elements || !formComplete) return;

    // Trigger form validation and wallet collection
    const { error: submitError } = await elements.submit();
    if (submitError) {
      // handle error
      console.log(submitError);
      return;
    }

    const { client_secret: clientSecret } = await createIntent();

    const { error } = await stripe.confirmSetup({
      elements,
      clientSecret,
      confirmParams: {
        return_url: `${location.protocol}//${location.host}/settings/billing/?checkout=success`,
      },
    });
    if (error) {
      setPaymentFormErrorMessage(error.message ?? "An error occurred");
    }
  };

  const handlePaymentElementChange = (
    event: StripePaymentElementChangeEvent,
  ) => {
    setFormComplete(event.complete);
  };

  return (
    <ModalBackdrop>
      <form
        action={formAction}
        className="w-[512px] bg-tertiary rounded-xl p-6 flex flex-col gap-6"
      >
        <div className="flex flex-col gap-2">
          <h2 className="text-content-2 text-xl leading-6 font-[500] -tracking-[0.01em]">
            You&apos;ve got credits!
          </h2>
          <h3 className="text-content-2 text-xs">
            You&apos;re almost there! Claim your $50 in free OpenHands credits
            by adding a credit card
          </h3>
          {paymentFormErrorMessage && (
            <h3 className="text-danger text-xs">{paymentFormErrorMessage}</h3>
          )}
        </div>

        <PaymentElement onChange={handlePaymentElementChange} />

        <BrandButton
          type="submit"
          variant="primary"
          className="w-full"
          isDisabled={!formComplete}
        >
          Confirm
        </BrandButton>
      </form>
    </ModalBackdrop>
  );
}
