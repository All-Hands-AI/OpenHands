import React, { useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "#/components/features/settings/brand-button";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import {
  BaseModalTitle,
  BaseModalDescription,
} from "#/components/shared/modals/confirmation-modals/base-modal";
import { SettingsInput } from "#/components/features/settings/settings-input";

interface ConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (workspace?: string) => void;
  platformName: string;
  isUnlinking: boolean;
}

export function ConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  platformName,
  isUnlinking,
}: ConfirmationModalProps) {
  const { t } = useTranslation();
  const [workspace, setWorkspace] = useState("");

  if (!isOpen) {
    return null;
  }

  const title = isUnlinking
    ? t(I18nKey.PROJECT_MANAGEMENT$UNLINK_CONFIRMATION_TITLE)
    : t(I18nKey.PROJECT_MANAGEMENT$LINK_CONFIRMATION_TITLE);

  const descriptionKey = isUnlinking
    ? I18nKey.PROJECT_MANAGEMENT$UNLINK_CONFIRMATION_DESCRIPTION
    : I18nKey.PROJECT_MANAGEMENT$LINK_CONFIRMATION_DESCRIPTION;

  if (!isOpen) {
    return null;
  }

  return (
    <ModalBackdrop onClose={onClose}>
      <ModalBody className="items-start border border-tertiary w-96">
        <BaseModalTitle title={title} />
        <BaseModalDescription>
          {t(descriptionKey, {
            platform: platformName,
          })}
          {!isUnlinking && (
            <p className="mt-4">
              <Trans
                i18nKey={
                  I18nKey.PROJECT_MANAGEMENT$IMPORTANT_WORKSPACE_INTEGRATION
                }
                components={{
                  b: <b />,
                  a: (
                    <a
                      href="https://docs.all-hands.dev/usage/cloud/openhands-cloud"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-500 underline"
                    >
                      Check the document for more information
                    </a>
                  ),
                }}
              />
            </p>
          )}
        </BaseModalDescription>
        {!isUnlinking && (
          <div className="w-full">
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
          </div>
        )}
        <div className="flex flex-col gap-2 w-full">
          <BrandButton
            onClick={() => onConfirm(workspace)}
            data-testid="confirm-button"
            type="button"
            variant="primary"
            className="w-full"
            isDisabled={!isUnlinking && !workspace.trim()}
          >
            {t(I18nKey.PROJECT_MANAGEMENT$CONFIRM_BUTTON_LABEL)}
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
