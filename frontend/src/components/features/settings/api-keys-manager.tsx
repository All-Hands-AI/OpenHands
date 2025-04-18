import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "#/components/features/settings/brand-button";
import { SettingsInput } from "#/components/features/settings/settings-input";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import ApiKeysClient, { ApiKey, CreateApiKeyResponse } from "#/api/api-keys";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";

export function ApiKeysManager() {
  const { t } = useTranslation();
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [keyToDelete, setKeyToDelete] = useState<ApiKey | null>(null);
  const [newlyCreatedKey, setNewlyCreatedKey] =
    useState<CreateApiKeyResponse | null>(null);
  const [showNewKeyModal, setShowNewKeyModal] = useState(false);

  const fetchApiKeys = async () => {
    try {
      setIsLoading(true);
      const keys = await ApiKeysClient.getApiKeys();
      // Ensure keys is always an array
      setApiKeys(Array.isArray(keys) ? keys : []);
    } catch (error) {
      displayErrorToast(
        retrieveAxiosErrorMessage(error as AxiosError) ||
          t(I18nKey.ERROR$GENERIC),
      );
      // Set empty array on error
      setApiKeys([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchApiKeys();
  }, []);

  const handleCreateKey = async () => {
    if (!newKeyName.trim()) {
      displayErrorToast(t(I18nKey.ERROR$REQUIRED_FIELD));
      return;
    }

    try {
      setIsCreating(true);
      const newKey = await ApiKeysClient.createApiKey(newKeyName);

      setNewlyCreatedKey(newKey);
      setCreateModalOpen(false);
      setShowNewKeyModal(true);
      await fetchApiKeys();
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

  const handleDeleteKey = async () => {
    if (!keyToDelete) return;

    try {
      setIsDeleting(true);
      await ApiKeysClient.deleteApiKey(keyToDelete.id);
      await fetchApiKeys();
      setDeleteModalOpen(false);
      setKeyToDelete(null);
      displaySuccessToast(t(I18nKey.SETTINGS$API_KEY_DELETED));
    } catch (error) {
      displayErrorToast(
        retrieveAxiosErrorMessage(error as AxiosError) ||
          t(I18nKey.ERROR$GENERIC),
      );
    } finally {
      setIsDeleting(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Never";
    return new Date(dateString).toLocaleString();
  };

  return (
    <>
      <div className="flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <BrandButton
            type="button"
            variant="primary"
            onClick={() => setCreateModalOpen(true)}
          >
            {t(I18nKey.SETTINGS$CREATE_API_KEY)}
          </BrandButton>
        </div>

        <p className="text-sm text-gray-300">
          {t(I18nKey.SETTINGS$API_KEYS_DESCRIPTION)}
        </p>

        {isLoading && (
          <div className="flex justify-center p-4">
            <LoadingSpinner size="large" />
          </div>
        )}
        {!isLoading && Array.isArray(apiKeys) && apiKeys.length > 0 && (
          <div className="border border-tertiary rounded-md overflow-hidden">
            <table className="w-full">
              <thead className="bg-base-tertiary">
                <tr>
                  <th className="text-left p-3 text-sm font-medium">
                    {t(I18nKey.SETTINGS$NAME)}
                  </th>
                  <th className="text-left p-3 text-sm font-medium">
                    {t(I18nKey.SETTINGS$KEY_PREFIX)}
                  </th>
                  <th className="text-left p-3 text-sm font-medium">
                    {t(I18nKey.SETTINGS$CREATED_AT)}
                  </th>
                  <th className="text-left p-3 text-sm font-medium">
                    {t(I18nKey.SETTINGS$LAST_USED)}
                  </th>
                  <th className="text-right p-3 text-sm font-medium">
                    {t(I18nKey.SETTINGS$ACTIONS)}
                  </th>
                </tr>
              </thead>
              <tbody>
                {apiKeys.map((key) => (
                  <tr key={key.id} className="border-t border-tertiary">
                    <td className="p-3 text-sm">{key.name}</td>
                    <td className="p-3 text-sm font-mono">{key.prefix}...</td>
                    <td className="p-3 text-sm">
                      {formatDate(key.created_at)}
                    </td>
                    <td className="p-3 text-sm">
                      {formatDate(key.last_used_at)}
                    </td>
                    <td className="p-3 text-right">
                      <button
                        className="underline"
                        onClick={() => {
                          setKeyToDelete(key);
                          setDeleteModalOpen(true);
                        }}
                      >
                        {t(I18nKey.BUTTON$DELETE)}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create API Key Modal */}
      {createModalOpen && (
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
                onClick={() => {
                  setCreateModalOpen(false);
                  setNewKeyName("");
                }}
                isDisabled={isCreating}
              >
                {t(I18nKey.BUTTON$CANCEL)}
              </BrandButton>
            </div>
          </div>
        </ModalBackdrop>
      )}

      {/* Delete API Key Modal */}
      {deleteModalOpen && keyToDelete && (
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
                onClick={() => {
                  setDeleteModalOpen(false);
                  setKeyToDelete(null);
                }}
                isDisabled={isDeleting}
              >
                {t(I18nKey.BUTTON$CANCEL)}
              </BrandButton>
            </div>
          </div>
        </ModalBackdrop>
      )}

      {/* Show New API Key Modal */}
      {showNewKeyModal && newlyCreatedKey && (
        <ModalBackdrop>
          <div
            data-testid="new-api-key-modal"
            className="bg-base-secondary p-6 rounded-xl flex flex-col gap-4 border border-tertiary w-[600px]"
          >
            <h3 className="text-xl font-bold">
              {t(I18nKey.SETTINGS$API_KEY_CREATED)}
            </h3>
            <p className="text-sm">
              {t(I18nKey.SETTINGS$API_KEY_WARNING)}
            </p>
            <div className="bg-base-tertiary p-4 rounded-md font-mono text-sm break-all">
              {newlyCreatedKey.key}
            </div>
            <div className="w-full flex gap-2 mt-2">
              <BrandButton
                type="button"
                variant="primary"
                onClick={() => {
                  navigator.clipboard.writeText(newlyCreatedKey.key);
                  displaySuccessToast(t(I18nKey.SETTINGS$API_KEY_COPIED));
                }}
              >
                {t(I18nKey.BUTTON$COPY_TO_CLIPBOARD)}
              </BrandButton>
              <BrandButton
                type="button"
                variant="secondary"
                onClick={() => {
                  setShowNewKeyModal(false);
                  setNewlyCreatedKey(null);
                }}
              >
                {t(I18nKey.BUTTON$CLOSE)}
              </BrandButton>
            </div>
          </div>
        </ModalBackdrop>
      )}
    </>
  );
}
