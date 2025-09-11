import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "#/components/features/settings/brand-button";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { useCancelSubscription } from "#/hooks/mutation/use-cancel-subscription";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";

interface CancelSubscriptionModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CancelSubscriptionModal({
  isOpen,
  onClose,
}: CancelSubscriptionModalProps) {
  const { t } = useTranslation();
  const cancelSubscriptionMutation = useCancelSubscription();

  const handleCancelSubscription = async () => {
    try {
      await cancelSubscriptionMutation.mutateAsync();
      displaySuccessToast(t(I18nKey.PAYMENT$SUBSCRIPTION_CANCELLED));
      onClose();
    } catch (error) {
      displayErrorToast(t(I18nKey.ERROR$GENERIC));
    }
  };

  if (!isOpen) return null;

  return (
    <ModalBackdrop>
      <div
        data-testid="cancel-subscription-modal"
        className="bg-base-secondary p-6 rounded-xl flex flex-col gap-4 border border-tertiary"
        style={{ width: "500px" }}
      >
        <h3 className="text-xl font-bold">
          {t(I18nKey.PAYMENT$CANCEL_SUBSCRIPTION_TITLE)}
        </h3>
        <p className="text-sm">
          {t(I18nKey.PAYMENT$CANCEL_SUBSCRIPTION_MESSAGE)}
        </p>
        <div className="w-full flex gap-2 mt-2">
          <BrandButton
            testId="confirm-cancel-button"
            type="button"
            variant="danger"
            className="grow"
            onClick={handleCancelSubscription}
            isDisabled={cancelSubscriptionMutation.isPending}
          >
            {cancelSubscriptionMutation.isPending ? (
              <LoadingSpinner size="small" />
            ) : (
              t(I18nKey.PAYMENT$CANCEL_SUBSCRIPTION)
            )}
          </BrandButton>
          <BrandButton
            testId="modal-cancel-button"
            type="button"
            variant="secondary"
            className="grow"
            onClick={onClose}
            isDisabled={cancelSubscriptionMutation.isPending}
          >
            {t(I18nKey.BUTTON$CANCEL)}
          </BrandButton>
        </div>
      </div>
    </ModalBackdrop>
  );
}
