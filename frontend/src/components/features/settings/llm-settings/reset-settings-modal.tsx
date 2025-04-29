import { useTranslation } from "react-i18next";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { I18nKey } from "#/i18n/declaration";
import { BrandButton } from "../brand-button";

interface ResetSettingsModalProps {
  onReset: () => void;
}

export function ResetSettingsModal({ onReset }: ResetSettingsModalProps) {
  const { t } = useTranslation();

  return (
    <ModalBackdrop>
      <div className="bg-base-secondary p-4 rounded-xl flex flex-col gap-4 border border-tertiary">
        <p>{t(I18nKey.SETTINGS$RESET_CONFIRMATION)}</p>
        <div className="w-full flex gap-2" data-testid="reset-settings-modal">
          <BrandButton
            testId="confirm-button"
            type="submit"
            name="reset-settings"
            variant="primary"
            className="grow"
          >
            Reset
          </BrandButton>

          <BrandButton
            testId="cancel-button"
            type="button"
            variant="secondary"
            className="grow"
            onClick={onReset}
          >
            Cancel
          </BrandButton>
        </div>
      </div>
    </ModalBackdrop>
  );
}
