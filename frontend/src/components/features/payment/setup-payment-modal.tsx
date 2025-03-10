import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import { useMutation } from "@tanstack/react-query";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import OpenHands from "#/api/open-hands";
import { BrandButton } from "../settings/brand-button";
import { LoadingSpinner } from "#/components/shared/loading-spinner";

export function SetupPaymentModal() {
  const { mutate, isPending } = useMutation({
    mutationFn: OpenHands.createBillingSessionResponse,
    onSuccess: (data) => {
      location.href = data
    },
  });

  return (
    <ModalBackdrop>
      <ModalBody className="border border-tertiary">
        <AllHandsLogo width={68} height={46} />
        <div className="flex flex-col gap-2 w-full items-center text-center">
          <h1 className="text-2xl font-bold">Get your Free OpenHands Credits.</h1>
          <p>TODO: Terms and conditions here (Or link to them)</p>
        </div>
        <BrandButton
          testId="enter-cc-details"
          type="submit"
          variant="primary"
          className="w-full"
          isDisabled={isPending}
          onClick={mutate}
        >
          Click here to Enter Payment details
        </BrandButton>
      </ModalBody>
    </ModalBackdrop>
  );
}
