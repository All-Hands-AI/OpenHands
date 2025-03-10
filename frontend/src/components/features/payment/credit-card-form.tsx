import React from "react";
import {
  PaymentElement,
  useElements,
  useStripe,
} from "@stripe/react-stripe-js";
import {
  StripePaymentElementChangeEvent
} from "@stripe/stripe-js";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { BrandButton } from "../settings/brand-button";

export function CreditCardForm() {
  const [formComplete, setFormComplete] = React.useState(false);
  const [paymentFormErrorMessage, setPaymentFormErrorMessage] =
    React.useState("");
  const stripe = useStripe();
  const elements = useElements();

  const formAction = async () => {
    setPaymentFormErrorMessage("");

    if (!stripe || !elements || !formComplete) return;

    const submitResult = await stripe.confirmSetup({
      elements,
      confirmParams: {
        return_url: window.location.href,
      },
    });
    const { error: submitError } = submitResult;
    if (submitError?.message) {
      setPaymentFormErrorMessage(submitError.message);
    }
  };

  const handlePaymentElementChange = (event: StripePaymentElementChangeEvent) => {
    setFormComplete(event.complete)
  }

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

        <BrandButton type="submit" variant="primary" className="w-full" isDisabled={!formComplete}>
          Confirm
        </BrandButton>
      </form>
    </ModalBackdrop>
  );
}
