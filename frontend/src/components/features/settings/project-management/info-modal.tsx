import React from "react";
import { Trans, useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "#/components/features/settings/brand-button";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import {
  BaseModalTitle,
  BaseModalDescription,
} from "#/components/shared/modals/confirmation-modals/base-modal";

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
      <ModalBody className="items-start border border-tertiary w-96">
        <BaseModalTitle
          title={t(I18nKey.PROJECT_MANAGEMENT$INFO_MODAL_TITLE)}
        />
        <BaseModalDescription>
          <Trans
            i18nKey={I18nKey.PROJECT_MANAGEMENT$INFO_MODAL_DESCRIPTION}
            values={{
              platform: platformName,
            }}
            components={{
              a: (
                <a
                  href="https://docs.all-hands.dev/usage/cloud/openhands-cloud"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:underline"
                >
                  documentation
                </a>
              ),
            }}
          />
        </BaseModalDescription>
        <div className="flex flex-col gap-2 w-full">
          <BrandButton
            variant="primary"
            onClick={onClose}
            data-testid="close-button"
            type="button"
            className="w-full"
          >
            {t(I18nKey.PROJECT_MANAGEMENT$CLOSE_BUTTON_LABEL)}
          </BrandButton>
        </div>
      </ModalBody>
    </ModalBackdrop>
  );
}
