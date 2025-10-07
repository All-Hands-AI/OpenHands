import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "#/components/features/settings/brand-button";
import { ModalBackdrop } from "./modal-backdrop";

interface ConfirmationModalProps {
  text: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmationModal({
  text,
  onConfirm,
  onCancel,
}: ConfirmationModalProps) {
  const { t } = useTranslation();
  return (
    <ModalBackdrop onClose={onCancel}>
      <div
        data-testid="confirmation-modal"
        className="bg-base-secondary p-4 rounded-xl flex flex-col gap-4 border border-tertiary"
      >
        <p>{text}</p>
        <div className="w-full flex gap-2">
          <BrandButton
            testId="cancel-button"
            type="button"
            onClick={onCancel}
            variant="secondary"
            className="grow"
          >
            {t(I18nKey.BUTTON$CANCEL)}
          </BrandButton>
          <BrandButton
            testId="confirm-button"
            type="button"
            onClick={onConfirm}
            variant="primary"
            className="grow"
          >
            {t(I18nKey.BUTTON$CONFIRM)}
          </BrandButton>
        </div>
      </div>
    </ModalBackdrop>
  );
}
