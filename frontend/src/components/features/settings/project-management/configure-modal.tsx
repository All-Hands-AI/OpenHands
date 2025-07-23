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
    !serviceAccountApiKey.trim();

  return (
    <ModalBackdrop onClose={onClose}>
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
          <SettingsInput
            label={t(I18nKey.PROJECT_MANAGEMENT$WORKSPACE_NAME_LABEL)}
            placeholder={t(
              I18nKey.PROJECT_MANAGEMENT$WORKSPACE_NAME_PLACEHOLDER,
            )}
            value={workspace}
            onChange={setWorkspace}
            className="w-full"
            type="text"
          />
          <SettingsInput
            label={t(I18nKey.PROJECT_MANAGEMENT$WEBHOOK_SECRET_LABEL)}
            placeholder={t(
              I18nKey.PROJECT_MANAGEMENT$WEBHOOK_SECRET_PLACEHOLDER,
            )}
            value={webhookSecret}
            onChange={setWebhookSecret}
            className="w-full"
            type="password"
          />
          <SettingsInput
            label={t(I18nKey.PROJECT_MANAGEMENT$SERVICE_ACCOUNT_EMAIL_LABEL)}
            placeholder={t(
              I18nKey.PROJECT_MANAGEMENT$SERVICE_ACCOUNT_EMAIL_PLACEHOLDER,
            )}
            value={serviceAccountEmail}
            onChange={setServiceAccountEmail}
            className="w-full"
            type="email"
          />
          <SettingsInput
            label={t(I18nKey.PROJECT_MANAGEMENT$SERVICE_ACCOUNT_API_LABEL)}
            placeholder={t(
              I18nKey.PROJECT_MANAGEMENT$SERVICE_ACCOUNT_API_PLACEHOLDER,
            )}
            value={serviceAccountApiKey}
            onChange={setServiceAccountApiKey}
            className="w-full"
            type="password"
          />
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
            onClick={onClose}
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
