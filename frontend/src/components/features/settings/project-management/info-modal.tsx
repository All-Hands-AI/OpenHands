import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "#/components/features/settings/brand-button";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";

interface InfoModalProps {
  isOpen: boolean;
  onClose: () => void;
  platformName: string;
}

export function InfoModal({ isOpen, onClose, platformName }: InfoModalProps) {
  const { t } = useTranslation();

  if (!isOpen) {
    return null;
  }

  return (
    <ModalBackdrop onClose={onClose}>
      <div className="bg-base-secondary p-4 rounded-xl flex flex-col gap-4 border border-tertiary w-96">
        <h2 className="text-lg font-semibold">
          {t(I18nKey.PROJECT_MANAGEMENT$INFO_MODAL_TITLE)}
        </h2>
        <p>
          {t(I18nKey.PROJECT_MANAGEMENT$INFO_MODAL_DESCRIPTION, {
            platform: platformName,
          })}
        </p>
        <div className="flex justify-end">
          <BrandButton
            variant="primary"
            onClick={onClose}
            data-testid="close-button"
            type="button"
          >
            {t(I18nKey.PROJECT_MANAGEMENT$CLOSE_BUTTON_LABEL)}
          </BrandButton>
        </div>
      </div>
    </ModalBackdrop>
  );
}
