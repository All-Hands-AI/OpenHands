import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "#/components/features/settings/brand-button";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import {
  BaseModalTitle,
  BaseModalDescription,
} from "#/components/shared/modals/confirmation-modals/base-modal";

interface ConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  platformName: string;
  isUnlinking: boolean;
}

export function ConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  platformName,
  isUnlinking,
}: ConfirmationModalProps) {
  const { t } = useTranslation();

  const title = isUnlinking
    ? t(I18nKey.PROJECT_MANAGEMENT$UNLINK_CONFIRMATION_TITLE)
    : t(I18nKey.PROJECT_MANAGEMENT$LINK_CONFIRMATION_TITLE);

  const descriptionKey = isUnlinking
    ? I18nKey.PROJECT_MANAGEMENT$UNLINK_CONFIRMATION_DESCRIPTION
    : I18nKey.PROJECT_MANAGEMENT$LINK_CONFIRMATION_DESCRIPTION;

  if (!isOpen) {
    return null;
  }

  return (
    <ModalBackdrop onClose={onClose}>
      <ModalBody className="items-start border border-tertiary w-96">
        <BaseModalTitle title={title} />
        <BaseModalDescription>
          {t(descriptionKey, {
            platform: platformName,
          })}
        </BaseModalDescription>
        <div className="flex flex-col gap-2 w-full">
          <BrandButton
            onClick={onConfirm}
            data-testid="confirm-button"
            type="button"
            variant="primary"
            className="w-full"
          >
            {t(I18nKey.PROJECT_MANAGEMENT$CONFIRM_BUTTON_LABEL)}
          </BrandButton>
          <BrandButton
            variant="secondary"
            onClick={onClose}
            data-testid="cancel-button"
            type="button"
            className="w-full"
          >
            {t(I18nKey.FEEDBACK$CANCEL_LABEL)}
          </BrandButton>
        </div>
      </ModalBody>
    </ModalBackdrop>
  );
}
