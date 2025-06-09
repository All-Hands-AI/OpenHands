import React, { useState } from "react";
import { useTranslation, Trans } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "#/components/features/settings/brand-button";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { ApiKey, CreateApiKeyResponse } from "#/api/api-keys";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import { CreateApiKeyModal } from "./create-api-key-modal";
import { DeleteApiKeyModal } from "./delete-api-key-modal";
import { NewApiKeyModal } from "./new-api-key-modal";
import { useApiKeys } from "#/hooks/query/use-api-keys";

export function ApiKeysManager() {
  const { t } = useTranslation();
  const { data: apiKeys = [], isLoading, error } = useApiKeys();
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [keyToDelete, setKeyToDelete] = useState<ApiKey | null>(null);
  const [newlyCreatedKey, setNewlyCreatedKey] =
    useState<CreateApiKeyResponse | null>(null);
  const [showNewKeyModal, setShowNewKeyModal] = useState(false);

  // Display error toast if the query fails
  if (error) {
    displayErrorToast(t(I18nKey.ERROR$GENERIC));
  }

  const handleKeyCreated = (newKey: CreateApiKeyResponse) => {
    setNewlyCreatedKey(newKey);
    setCreateModalOpen(false);
    setShowNewKeyModal(true);
  };

  const handleCloseCreateModal = () => {
    setCreateModalOpen(false);
  };

  const handleCloseDeleteModal = () => {
    setDeleteModalOpen(false);
    setKeyToDelete(null);
  };

  const handleCloseNewKeyModal = () => {
    setShowNewKeyModal(false);
    setNewlyCreatedKey(null);
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
          <Trans
            i18nKey={I18nKey.SETTINGS$API_KEYS_DESCRIPTION}
            components={{
              a: (
                <a
                  href="https://docs.all-hands.dev/usage/cloud/cloud-api"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:underline"
                >
                  API documentation
                </a>
              ),
            }}
          />
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
                    <td className="p-3 text-sm">
                      {formatDate(key.created_at)}
                    </td>
                    <td className="p-3 text-sm">
                      {formatDate(key.last_used_at)}
                    </td>
                    <td className="p-3 text-right">
                      <button
                        type="button"
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
      <CreateApiKeyModal
        isOpen={createModalOpen}
        onClose={handleCloseCreateModal}
        onKeyCreated={handleKeyCreated}
      />

      {/* Delete API Key Modal */}
      <DeleteApiKeyModal
        isOpen={deleteModalOpen}
        keyToDelete={keyToDelete}
        onClose={handleCloseDeleteModal}
      />

      {/* Show New API Key Modal */}
      <NewApiKeyModal
        isOpen={showNewKeyModal}
        newlyCreatedKey={newlyCreatedKey}
        onClose={handleCloseNewKeyModal}
      />
    </>
  );
}
