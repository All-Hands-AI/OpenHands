import React, { useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "#/components/features/settings/brand-button";
import { SettingsInput } from "#/components/features/settings/settings-input";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import {
  BaseModalDescription,
  BaseModalTitle,
} from "#/components/shared/modals/confirmation-modals/base-modal";
import { SettingsSwitch } from "#/components/features/settings/settings-switch";

interface ConfigureButtonProps {
  onClick: () => void;
  isDisabled: boolean;
  "data-testid"?: string;
}

export function ConfigureButton({
  onClick,
  isDisabled,
  "data-testid": dataTestId,
}: ConfigureButtonProps) {
  const { t } = useTranslation();
  return (
    <BrandButton
      data-testid={dataTestId}
      variant="primary"
      onClick={onClick}
      isDisabled={isDisabled}
      type="button"
      className="w-30 min-w-20"
    >
      {t(I18nKey.PROJECT_MANAGEMENT$CONFIGURE_BUTTON_LABEL)}
    </BrandButton>
  );
}

interface ConfigureModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (data: {
    workspace: string;
    webhookSecret: string;
    serviceAccountEmail: string;
    serviceAccountApiKey: string;
    isActive: boolean;
  }) => void;
  platformName: string;
}

export function ConfigureModal({
  isOpen,
  onClose,
  onConfirm,
  platformName,
}: ConfigureModalProps) {
  const { t } = useTranslation();
  const [workspace, setWorkspace] = useState("");
  const [webhookSecret, setWebhookSecret] = useState("");
  const [serviceAccountEmail, setServiceAccountEmail] = useState("");
  const [serviceAccountApiKey, setServiceAccountApiKey] = useState("");
  const [isActive, setIsActive] = useState(false);

  // Validation states
  const [workspaceError, setWorkspaceError] = useState<string | null>(null);
  const [webhookSecretError, setWebhookSecretError] = useState<string | null>(
    null,
  );
  const [emailError, setEmailError] = useState<string | null>(null);
  const [apiKeyError, setApiKeyError] = useState<string | null>(null);

  // Validation functions
  const validateWorkspace = (value: string) => {
    const isValid = /^[a-zA-Z0-9\-_.]*$/.test(value);
    if (!isValid && value.length > 0) {
      setWorkspaceError(
        t(I18nKey.PROJECT_MANAGEMENT$WORKSPACE_NAME_VALIDATION_ERROR),
      );
    } else {
      setWorkspaceError(null);
    }
    return isValid;
  };

  const validateWebhookSecret = (value: string) => {
    const hasSpaces = /\s/.test(value);
    if (hasSpaces) {
      setWebhookSecretError(
        t(I18nKey.PROJECT_MANAGEMENT$WORKSPACE_NAME_VALIDATION_ERROR),
      );
    } else {
      setWebhookSecretError(null);
    }
    return !hasSpaces;
  };

  const validateEmail = (value: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isValid = emailRegex.test(value) || value.length === 0;
    if (!isValid && value.length > 0) {
      setEmailError(
        t(I18nKey.PROJECT_MANAGEMENT$WORKSPACE_NAME_VALIDATION_ERROR),
      );
    } else {
      setEmailError(null);
    }
    return isValid;
  };

  const validateApiKey = (value: string) => {
    const hasSpaces = /\s/.test(value);
    if (hasSpaces) {
      setApiKeyError(
        t(I18nKey.PROJECT_MANAGEMENT$WORKSPACE_NAME_VALIDATION_ERROR),
      );
    } else {
      setApiKeyError(null);
    }
    return !hasSpaces;
  };

  // Input handlers with validation
  const handleWorkspaceChange = (value: string) => {
    setWorkspace(value);
    validateWorkspace(value);
  };

  const handleWebhookSecretChange = (value: string) => {
    setWebhookSecret(value);
    validateWebhookSecret(value);
  };

  const handleEmailChange = (value: string) => {
    setServiceAccountEmail(value);
    validateEmail(value);
  };

  const handleApiKeyChange = (value: string) => {
    setServiceAccountApiKey(value);
    validateApiKey(value);
  };

  const handleClose = () => {
    setWorkspace("");
    setWebhookSecret("");
    setServiceAccountEmail("");
    setServiceAccountApiKey("");
    setIsActive(false);
    setWorkspaceError(null);
    setWebhookSecretError(null);
    setEmailError(null);
    setApiKeyError(null);
    onClose();
  };

  if (!isOpen) {
    return null;
  }

  const handleConnect = () => {
    onConfirm({
      workspace,
      webhookSecret,
      serviceAccountEmail,
      serviceAccountApiKey,
      isActive,
    });
  };

  const isConnectDisabled =
    !workspace.trim() ||
    !webhookSecret.trim() ||
    !serviceAccountEmail.trim() ||
    !serviceAccountApiKey.trim() ||
    workspaceError !== null ||
    webhookSecretError !== null ||
    emailError !== null ||
    apiKeyError !== null;

  return (
    <ModalBackdrop onClose={handleClose}>
      <ModalBody className="items-start border border-tertiary w-96">
        <BaseModalTitle title={`Configure ${platformName}`} />
        <BaseModalDescription>
          <Trans
            i18nKey={I18nKey.PROJECT_MANAGEMENT$CONFIGURE_MODAL_DESCRIPTION}
            components={{
              a: (
                <a
                  href="https://docs.all-hands.dev/usage/cloud/openhands-cloud"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-500 hover:underline"
                >
                  Check the document for more information
                </a>
              ),
              b: <b />,
            }}
          />
        </BaseModalDescription>
        <div className="w-full flex flex-col gap-4 mt-4">
          <div>
            <SettingsInput
              label={t(I18nKey.PROJECT_MANAGEMENT$WORKSPACE_NAME_LABEL)}
              placeholder={t(
                I18nKey.PROJECT_MANAGEMENT$WORKSPACE_NAME_PLACEHOLDER,
              )}
              value={workspace}
              onChange={handleWorkspaceChange}
              className="w-full"
              type="text"
              pattern="^[a-zA-Z0-9\-_.]*$"
            />
            {workspaceError && (
              <p className="text-red-500 text-sm mt-2">{workspaceError}</p>
            )}
          </div>
          <div>
            <SettingsInput
              label={t(I18nKey.PROJECT_MANAGEMENT$WEBHOOK_SECRET_LABEL)}
              placeholder={t(
                I18nKey.PROJECT_MANAGEMENT$WEBHOOK_SECRET_PLACEHOLDER,
              )}
              value={webhookSecret}
              onChange={handleWebhookSecretChange}
              className="w-full"
              type="password"
            />
            {webhookSecretError && (
              <p className="text-red-500 text-sm mt-2">{webhookSecretError}</p>
            )}
          </div>
          <div>
            <SettingsInput
              label={t(I18nKey.PROJECT_MANAGEMENT$SERVICE_ACCOUNT_EMAIL_LABEL)}
              placeholder={t(
                I18nKey.PROJECT_MANAGEMENT$SERVICE_ACCOUNT_EMAIL_PLACEHOLDER,
              )}
              value={serviceAccountEmail}
              onChange={handleEmailChange}
              className="w-full"
              type="email"
            />
            {emailError && (
              <p className="text-red-500 text-sm mt-2">{emailError}</p>
            )}
          </div>
          <div>
            <SettingsInput
              label={t(I18nKey.PROJECT_MANAGEMENT$SERVICE_ACCOUNT_API_LABEL)}
              placeholder={t(
                I18nKey.PROJECT_MANAGEMENT$SERVICE_ACCOUNT_API_PLACEHOLDER,
              )}
              value={serviceAccountApiKey}
              onChange={handleApiKeyChange}
              className="w-full"
              type="password"
            />
            {apiKeyError && (
              <p className="text-red-500 text-sm mt-2">{apiKeyError}</p>
            )}
          </div>
          <div className="mt-4">
            <SettingsSwitch
              testId="active-toggle"
              onToggle={setIsActive}
              isToggled={isActive}
            >
              {t(I18nKey.PROJECT_MANAGEMENT$ACTIVE_TOGGLE_LABEL)}
            </SettingsSwitch>
          </div>
        </div>
        <div className="flex flex-col gap-2 w-full mt-4">
          <BrandButton
            variant="primary"
            onClick={handleConnect}
            data-testid="connect-button"
            type="button"
            className="w-full"
            isDisabled={isConnectDisabled}
          >
            {t(I18nKey.PROJECT_MANAGEMENT$CONNECT_BUTTON_LABEL)}
          </BrandButton>
          <BrandButton
            variant="secondary"
            onClick={handleClose}
            data-testid="cancel-button"
            type="button"
            className="w-full"
          >
            {t(I18nKey.FEEDBACK$CANCEL_LABEL)}
          </BrandButton>
        </div>
      </ModalBody>
    </ModalBackdrop>
  );
}
