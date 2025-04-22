import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "#/components/features/settings/brand-button";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { CreateApiKeyResponse } from "#/api/api-keys";
import { displaySuccessToast } from "#/utils/custom-toast-handlers";

interface NewApiKeyModalProps {
  isOpen: boolean;
  newlyCreatedKey: CreateApiKeyResponse | null;
  onClose: () => void;
}

export function NewApiKeyModal({
  isOpen,
  newlyCreatedKey,
  onClose,
}: NewApiKeyModalProps) {
  const { t } = useTranslation();

  const handleCopyToClipboard = () => {
    if (newlyCreatedKey) {
      navigator.clipboard.writeText(newlyCreatedKey.key);
      displaySuccessToast(t(I18nKey.SETTINGS$API_KEY_COPIED));
    }
  };

  if (!isOpen || !newlyCreatedKey) return null;

  return (
    <ModalBackdrop>
      <div
        data-testid="new-api-key-modal"
        className="bg-base-secondary p-6 rounded-xl flex flex-col gap-4 border border-tertiary w-[600px]"
      >
        <h3 className="text-xl font-bold">
          {t(I18nKey.SETTINGS$API_KEY_CREATED)}
        </h3>
        <p className="text-sm">{t(I18nKey.SETTINGS$API_KEY_WARNING)}</p>
        <div className="bg-base-tertiary p-4 rounded-md font-mono text-sm break-all">
          {newlyCreatedKey.key}
        </div>
        <div className="w-full flex gap-2 mt-2">
          <BrandButton
            type="button"
            variant="primary"
            onClick={handleCopyToClipboard}
          >
            {t(I18nKey.BUTTON$COPY_TO_CLIPBOARD)}
          </BrandButton>
          <BrandButton type="button" variant="secondary" onClick={onClose}>
            {t(I18nKey.BUTTON$CLOSE)}
          </BrandButton>
        </div>
      </div>
    </ModalBackdrop>
  );
}
