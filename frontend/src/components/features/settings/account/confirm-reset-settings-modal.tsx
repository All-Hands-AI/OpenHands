import { useTranslation } from "react-i18next";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "../brand-button";

interface ConfirmResetSettingsModalProps {
  handleReset: () => void;
  onClose: () => void;
}

export function ConfirmResetSettingsModal({
  handleReset,
  onClose,
}: ConfirmResetSettingsModalProps) {
  const { t } = useTranslation();

  return (
    <ModalBackdrop>
      <div
        data-testid="reset-modal"
        className="bg-base-secondary p-4 rounded-xl flex flex-col gap-4 border border-tertiary"
      >
        <p>{t(I18nKey.SETTINGS$RESET_CONFIRMATION)}</p>
        <div className="w-full flex gap-2">
          <BrandButton
            type="button"
            variant="primary"
            className="grow"
            onClick={handleReset}
          >
            Reset
          </BrandButton>

          <BrandButton
            type="button"
            variant="secondary"
            className="grow"
            onClick={onClose}
          >
            Cancel
          </BrandButton>
        </div>
      </div>
    </ModalBackdrop>
  );
}
