import { useTranslation } from "react-i18next";
import { Checkbox } from "@openhands/ui";
import { useState } from "react";
import {
  BaseModalTitle,
  BaseModalDescription,
} from "#/components/shared/modals/confirmation-modals/base-modal";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import { handleCaptureConsent } from "#/utils/handle-capture-consent";
import { BrandButton } from "../settings/brand-button";
import { I18nKey } from "#/i18n/declaration";

interface AnalyticsConsentFormModalProps {
  onClose: () => void;
}

export function AnalyticsConsentFormModal({
  onClose,
}: AnalyticsConsentFormModalProps) {
  const { t } = useTranslation();
  const { mutate: saveUserSettings } = useSaveSettings();
  const [checked, setChecked] = useState(true);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const analytics = formData.get("analytics") === "on";

    saveUserSettings(
      { user_consents_to_analytics: analytics },
      {
        onSuccess: () => {
          handleCaptureConsent(analytics);
          onClose();
        },
      },
    );
  };

  return (
    <ModalBackdrop>
      <form
        data-testid="user-capture-consent-form"
        onSubmit={handleSubmit}
        className="flex flex-col gap-2"
      >
        <ModalBody className="border border-tertiary">
          <BaseModalTitle title={t(I18nKey.ANALYTICS$TITLE)} />
          <BaseModalDescription>
            {t(I18nKey.ANALYTICS$DESCRIPTION)}
          </BaseModalDescription>
          <Checkbox
            checked={checked}
            className="flex gap-2 items-center self-start"
            name="analytics"
            onChange={(e) => setChecked(e.target.checked)}
            label={t(I18nKey.ANALYTICS$SEND_ANONYMOUS_DATA)}
          />

          <BrandButton
            testId="confirm-preferences"
            type="submit"
            variant="primary"
            className="w-full"
          >
            {t(I18nKey.ANALYTICS$CONFIRM_PREFERENCES)}
          </BrandButton>
        </ModalBody>
      </form>
    </ModalBackdrop>
  );
}
