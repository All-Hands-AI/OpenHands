import React, { useState } from "react";
import { useTranslation, Trans } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "#/components/features/settings/brand-button";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { ApiKey, CreateApiKeyResponse } from "#/api/api-keys";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";
import { CreateApiKeyModal } from "./create-api-key-modal";
import { DeleteApiKeyModal } from "./delete-api-key-modal";
import { NewApiKeyModal } from "./new-api-key-modal";
import { useApiKeys } from "#/hooks/query/use-api-keys";
import {
  useLlmApiKey,
  useRefreshLlmApiKey,
} from "#/hooks/query/use-llm-api-key";

export function ApiKeysManager() {
  const { t } = useTranslation();
  const { data: apiKeys = [], isLoading, error } = useApiKeys();
  const { data: llmApiKey, isLoading: isLoadingLlmKey } = useLlmApiKey();
  const refreshLlmApiKey = useRefreshLlmApiKey();
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [keyToDelete, setKeyToDelete] = useState<ApiKey | null>(null);
  const [newlyCreatedKey, setNewlyCreatedKey] =
    useState<CreateApiKeyResponse | null>(null);
  const [showNewKeyModal, setShowNewKeyModal] = useState(false);
  const [isRefreshingLlmKey, setIsRefreshingLlmKey] = useState(false);
  const [showLlmApiKey, setShowLlmApiKey] = useState(false);

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

  const handleRefreshLlmApiKey = async () => {
    try {
      setIsRefreshingLlmKey(true);
      await refreshLlmApiKey.mutateAsync();
      displaySuccessToast(
        t(I18nKey.SETTINGS$API_KEY_REFRESHED, {
          defaultValue: "API key refreshed successfully",
        }),
      );
    } catch (err) {
      displayErrorToast(t(I18nKey.ERROR$GENERIC));
    } finally {
      setIsRefreshingLlmKey(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Never";
    return new Date(dateString).toLocaleString();
  };

  return (
    <>
      <div className="flex flex-col gap-6">
        {!isLoadingLlmKey && llmApiKey && (
          <div className="border-b border-gray-200 pb-6 mb-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xl font-medium text-white">
                {t(I18nKey.SETTINGS$LLM_API_KEY)}
              </h3>
              <BrandButton
                type="button"
                variant="primary"
                onClick={handleRefreshLlmApiKey}
                isDisabled={isRefreshingLlmKey}
              >
                {isRefreshingLlmKey ? (
                  <LoadingSpinner size="small" />
                ) : (
                  t(I18nKey.SETTINGS$REFRESH_LLM_API_KEY)
                )}
              </BrandButton>
            </div>
            <p className="text-sm text-white mb-4">
              {t(I18nKey.SETTINGS$LLM_API_KEY_DESCRIPTION)}
            </p>
            <div className="flex items-center gap-2 mt-4">
              <div className="flex-1 bg-base-tertiary rounded-md py-2 flex items-center">
                <div className="flex-1 pl-2">
                  {llmApiKey.key ? (
                    <div className="flex items-center">
                      {showLlmApiKey ? (
                        <span className="text-white font-mono">
                          {llmApiKey.key}
                        </span>
                      ) : (
                        <span className="text-white">{"•".repeat(20)}</span>
                      )}
                    </div>
                  ) : (
                    <span className="text-white">
                      {t(I18nKey.API$NO_KEY_AVAILABLE)}
                    </span>
                  )}
                </div>
                <div className="flex items-center">
                  {llmApiKey.key && (
                    <button
                      type="button"
                      className="text-white hover:text-gray-300 mr-2"
                      aria-label={
                        showLlmApiKey ? "Hide API key" : "Show API key"
                      }
                      title={showLlmApiKey ? "Hide API key" : "Show API key"}
                      onClick={() => setShowLlmApiKey(!showLlmApiKey)}
                    >
                      {showLlmApiKey ? (
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          width="20"
                          height="20"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        >
                          <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                          <line x1="1" y1="1" x2="23" y2="23" />
                        </svg>
                      ) : (
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          width="20"
                          height="20"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        >
                          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                          <circle cx="12" cy="12" r="3" />
                        </svg>
                      )}
                    </button>
                  )}
                  <button
                    type="button"
                    className="text-white hover:text-gray-300 mr-2"
                    aria-label="Copy API key"
                    title="Copy API key"
                    onClick={() => {
                      if (llmApiKey.key) {
                        navigator.clipboard.writeText(llmApiKey.key);
                        displaySuccessToast(t(I18nKey.SETTINGS$API_KEY_COPIED));
                      }
                    }}
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="20"
                      height="20"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        <h3 className="text-xl font-medium text-white">
          {t(I18nKey.SETTINGS$OPENHANDS_API_KEYS)}
        </h3>

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
                    <td
                      className="p-3 text-sm truncate max-w-[160px]"
                      title={key.name}
                    >
                      {key.name}
                    </td>
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
