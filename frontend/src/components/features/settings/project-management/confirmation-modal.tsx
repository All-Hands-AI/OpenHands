import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "#/components/features/settings/brand-button";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";

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
      <div className="bg-base-secondary p-4 rounded-xl flex flex-col gap-4 border border-tertiary w-96">
        <h2 className="text-lg font-semibold">{title}</h2>
        <p>
          {t(descriptionKey, {
            platform: platformName,
          })}
        </p>
        <div className="flex justify-end gap-2">
          <BrandButton
            variant="secondary"
            onClick={onClose}
            data-testid="cancel-button"
            type="button"
          >
            {t(I18nKey.FEEDBACK$CANCEL_LABEL)}
          </BrandButton>
          <BrandButton
            onClick={onConfirm}
            data-testid="confirm-button"
            type="button"
            variant="primary"
          >
            {t(I18nKey.PROJECT_MANAGEMENT$CONFIRM_BUTTON_LABEL)}
          </BrandButton>
        </div>
      </div>
    </ModalBackdrop>
  );
}
