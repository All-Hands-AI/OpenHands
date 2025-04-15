import { useTranslation } from "react-i18next"
import {
  BaseModalDescription,
  BaseModalTitle,
} from "#/components/shared/modals/confirmation-modals/base-modal"
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop"
import { ModalBody } from "#/components/shared/modals/modal-body"
import { BrandButton } from "../settings/brand-button"
import { I18nKey } from "#/i18n/declaration"

interface ConfirmDeleteModalProps {
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmDeleteModal({
  onConfirm,
  onCancel,
}: ConfirmDeleteModalProps) {
  const { t } = useTranslation()

  return (
    <ModalBackdrop>
      <ModalBody className="items-start border border-neutral-1000">
        <div className="flex flex-col gap-2">
          <BaseModalTitle title={t(I18nKey.CONVERSATION$CONFIRM_DELETE)} />
          <BaseModalDescription
            description={t(I18nKey.CONVERSATION$DELETE_WARNING)}
          />
        </div>
        <div
          className="flex w-full flex-col gap-2"
          onClick={(event) => event.stopPropagation()}
        >
          <BrandButton
            type="button"
            variant="primary"
            onClick={onConfirm}
            className="w-full"
            data-testid="confirm-button"
          >
            {t(I18nKey.ACTION$CONFIRM)}
          </BrandButton>
          <BrandButton
            type="button"
            variant="secondary"
            onClick={onCancel}
            className="w-full"
            data-testid="cancel-button"
          >
            {t(I18nKey.BUTTON$CANCEL)}
          </BrandButton>
        </div>
      </ModalBody>
    </ModalBackdrop>
  )
}
