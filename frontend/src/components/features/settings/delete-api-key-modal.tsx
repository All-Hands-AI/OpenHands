import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "#/components/features/settings/brand-button";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import ApiKeysClient, { ApiKey } from "#/api/api-keys";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";

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

  if (!isOpen || !keyToDelete) return null;

  return (
    <ModalBackdrop>
      <div
        data-testid="delete-api-key-modal"
        className="bg-base-secondary p-6 rounded-xl flex flex-col gap-4 border border-tertiary w-[500px]"
      >
        <h3 className="text-xl font-bold">
          {t(I18nKey.SETTINGS$DELETE_API_KEY)}
        </h3>
        <p className="text-sm">
          {t(I18nKey.SETTINGS$DELETE_API_KEY_CONFIRMATION, {
            name: keyToDelete.name,
          })}
        </p>
        <div className="w-full flex gap-2 mt-2">
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
        </div>
      </div>
    </ModalBackdrop>
  );
}
