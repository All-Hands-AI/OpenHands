import { useTranslation } from "react-i18next";
import { useState } from "react";
import {
  BaseModalDescription,
  BaseModalTitle,
} from "#/components/shared/modals/confirmation-modals/base-modal";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import { BrandButton } from "../settings/brand-button";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { I18nKey } from "#/i18n/declaration";

interface ConfirmResetModalProps {
  onConfirm: (deleteOldConversation: boolean) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export function ConfirmResetModal({
  onConfirm,
  onCancel,
  isLoading = false,
}: ConfirmResetModalProps) {
  const { t } = useTranslation();
  const [deleteOldConversation, setDeleteOldConversation] = useState(false);

  return (
    <ModalBackdrop>
      <ModalBody className="items-start border border-tertiary">
        <div className="flex flex-col gap-2">
          <BaseModalTitle title={t(I18nKey.MODAL$CONFIRM_RESET_TITLE)} />
          <BaseModalDescription
            description={t(I18nKey.CONVERSATION$RESET_WARNING)}
          />
          <div className="flex items-center gap-2 mt-2">
            <input
              type="checkbox"
              id="delete-old-conversation"
              checked={deleteOldConversation}
              onChange={(e) => setDeleteOldConversation(e.target.checked)}
              disabled={isLoading}
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            />
            <label
              htmlFor="delete-old-conversation"
              className="text-sm text-gray-700"
            >
              {t(I18nKey.CONVERSATION$DELETE_OLD_CONVERSATION)}
            </label>
          </div>
        </div>
        <div
          className="flex flex-col gap-2 w-full"
          onClick={(event) => event.stopPropagation()}
        >
          <BrandButton
            type="button"
            variant="primary"
            onClick={() => onConfirm(deleteOldConversation)}
            className="w-full"
            data-testid="confirm-button"
            isDisabled={isLoading}
          >
            {isLoading ? (
              <div className="flex items-center justify-center gap-2">
                <LoadingSpinner size="small" />
                <span>{t(I18nKey.HOME$LOADING)}</span>
              </div>
            ) : (
              t(I18nKey.ACTION$CONFIRM)
            )}
          </BrandButton>
          <BrandButton
            type="button"
            variant="secondary"
            onClick={onCancel}
            className="w-full"
            data-testid="cancel-button"
            isDisabled={isLoading}
          >
            {t(I18nKey.BUTTON$CANCEL)}
          </BrandButton>
        </div>
      </ModalBody>
    </ModalBackdrop>
  );
}
