import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "#/components/features/settings/brand-button";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import ApiKeysClient, { ApiKey } from "#/api/api-keys";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";
import { ApiKeyModalBase } from "./api-key-modal-base";

interface DeleteApiKeyModalProps {
  isOpen: boolean;
  keyToDelete: ApiKey | null;
  onClose: () => void;
  onRefresh: () => Promise<void>;
}

export function DeleteApiKeyModal({
  isOpen,
  keyToDelete,
  onClose,
  onRefresh,
}: DeleteApiKeyModalProps) {
  const { t } = useTranslation();
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDeleteKey = async () => {
    if (!keyToDelete) return;

    try {
      setIsDeleting(true);
      await ApiKeysClient.deleteApiKey(keyToDelete.id);
      await onRefresh();
      displaySuccessToast(t(I18nKey.SETTINGS$API_KEY_DELETED));
      onClose();
    } catch (error) {
      displayErrorToast(
        retrieveAxiosErrorMessage(error as AxiosError) ||
          t(I18nKey.ERROR$GENERIC),
      );
    } finally {
      setIsDeleting(false);
    }
  };

  if (!keyToDelete) return null;

  const modalFooter = (
    <>
      <BrandButton
        type="button"
        variant="danger"
        className="grow"
        onClick={handleDeleteKey}
        isDisabled={isDeleting}
      >
        {isDeleting ? (
          <LoadingSpinner size="small" />
        ) : (
          t(I18nKey.BUTTON$DELETE)
        )}
      </BrandButton>
      <BrandButton
        type="button"
        variant="secondary"
        className="grow"
        onClick={onClose}
        isDisabled={isDeleting}
      >
        {t(I18nKey.BUTTON$CANCEL)}
      </BrandButton>
    </>
  );

  return (
    <ApiKeyModalBase
      isOpen={isOpen && !!keyToDelete}
      title={t(I18nKey.SETTINGS$DELETE_API_KEY)}
      footer={modalFooter}
    >
      <div data-testid="delete-api-key-modal">
        <p className="text-sm">
          {t(I18nKey.SETTINGS$DELETE_API_KEY_CONFIRMATION, {
            name: keyToDelete.name,
          })}
        </p>
      </div>
    </ApiKeyModalBase>
  );
}
