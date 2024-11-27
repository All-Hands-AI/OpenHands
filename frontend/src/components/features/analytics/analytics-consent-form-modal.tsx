import { ModalButton } from "#/components/shared/buttons/modal-button";
import {
  BaseModalTitle,
  BaseModalDescription,
} from "#/components/shared/modals/confirmation-modals/base-modal";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import { handleCaptureConsent } from "#/utils/handle-capture-consent";

interface AnalyticsConsentFormModalProps {
  onClose: () => void;
}

export function AnalyticsConsentFormModal({
  onClose,
}: AnalyticsConsentFormModalProps) {
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const analytics = formData.get("analytics") === "on";

    handleCaptureConsent(analytics);
    localStorage.setItem("analytics-consent", analytics.toString());

    onClose();
  };

  return (
    <ModalBackdrop>
      <form
        data-testid="user-capture-consent-form"
        onSubmit={handleSubmit}
        className="flex flex-col gap-2"
      >
        <ModalBody>
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

          <ModalButton
            type="submit"
            text="Confirm Preferences"
            className="bg-primary text-white w-full hover:opacity-80"
          />
        </ModalBody>
      </form>
    </ModalBackdrop>
  );
}
