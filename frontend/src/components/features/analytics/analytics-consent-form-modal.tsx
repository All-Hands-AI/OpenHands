import {
  BaseModalTitle,
  BaseModalDescription,
} from "#/components/shared/modals/confirmation-modals/base-modal";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import { useCurrentSettings } from "#/context/settings-context";
import { handleCaptureConsent } from "#/utils/handle-capture-consent";
import { BrandButton } from "../settings/brand-button";

interface AnalyticsConsentFormModalProps {
  onClose: () => void;
}

export function AnalyticsConsentFormModal({
  onClose,
}: AnalyticsConsentFormModalProps) {
  const { saveUserSettings } = useCurrentSettings();

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const analytics = formData.get("analytics") === "on";

    await saveUserSettings(
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
          <BaseModalTitle title="Your Privacy Preferences" />
          <BaseModalDescription>
            We use tools to understand how our application is used to improve
            your experience. You can enable or disable analytics. Your
            preferences will be stored and can be updated anytime.
          </BaseModalDescription>

          <label className="flex gap-2 items-center self-start">
            <input name="analytics" type="checkbox" defaultChecked />
            Send anonymous usage data
          </label>

          <BrandButton
            testId="confirm-preferences"
            type="submit"
            variant="primary"
            className="w-full"
          >
            Confirm Preferences
          </BrandButton>
        </ModalBody>
      </form>
    </ModalBackdrop>
  );
}
