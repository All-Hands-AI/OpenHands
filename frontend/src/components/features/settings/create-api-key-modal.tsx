import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "#/components/features/settings/brand-button";
import { SettingsInput } from "#/components/features/settings/settings-input";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import ApiKeysClient, { CreateApiKeyResponse } from "#/api/api-keys";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";

interface CreateApiKeyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onKeyCreated: (newKey: CreateApiKeyResponse) => void;
  onRefresh: () => Promise<void>;
}

export function CreateApiKeyModal({
  isOpen,
  onClose,
  onKeyCreated,
  onRefresh,
}: CreateApiKeyModalProps) {
  const { t } = useTranslation();
  const [newKeyName, setNewKeyName] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  const handleCreateKey = async () => {
    if (!newKeyName.trim()) {
      displayErrorToast(t(I18nKey.ERROR$REQUIRED_FIELD));
      return;
    }

    try {
      setIsCreating(true);
      const newKey = await ApiKeysClient.createApiKey(newKeyName);

      onKeyCreated(newKey);
      await onRefresh();
      displaySuccessToast(t(I18nKey.SETTINGS$API_KEY_CREATED));
    } catch (error) {
      displayErrorToast(
        retrieveAxiosErrorMessage(error as AxiosError) ||
          t(I18nKey.ERROR$GENERIC),
      );
    } finally {
      setIsCreating(false);
      setNewKeyName("");
    }
  };

  const handleCancel = () => {
    setNewKeyName("");
    onClose();
  };

  if (!isOpen) return null;

  return (
    <ModalBackdrop>
      <div
        data-testid="create-api-key-modal"
        className="bg-base-secondary p-6 rounded-xl flex flex-col gap-4 border border-tertiary w-[500px]"
      >
        <h3 className="text-xl font-bold">
          {t(I18nKey.SETTINGS$CREATE_API_KEY)}
        </h3>
        <p className="text-sm text-gray-300">
          {t(I18nKey.SETTINGS$CREATE_API_KEY_DESCRIPTION)}
        </p>
        <SettingsInput
          testId="api-key-name-input"
          label={t(I18nKey.SETTINGS$NAME)}
          placeholder={t(I18nKey.SETTINGS$API_KEY_NAME_PLACEHOLDER)}
          value={newKeyName}
          onChange={(value) => setNewKeyName(value)}
          className="w-full"
          type="text"
        />
        <div className="w-full flex gap-2 mt-2">
          <BrandButton
            type="button"
            variant="primary"
            className="grow"
            onClick={handleCreateKey}
            isDisabled={isCreating || !newKeyName.trim()}
          >
            {isCreating ? (
              <LoadingSpinner size="small" />
            ) : (
              t(I18nKey.BUTTON$CREATE)
            )}
          </BrandButton>
          <BrandButton
            type="button"
            variant="secondary"
            className="grow"
            onClick={handleCancel}
            isDisabled={isCreating}
          >
            {t(I18nKey.BUTTON$CANCEL)}
          </BrandButton>
        </div>
      </div>
    </ModalBackdrop>
  );
}
