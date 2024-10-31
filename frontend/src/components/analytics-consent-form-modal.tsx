import { useFetcher } from "@remix-run/react";
import { ModalBackdrop } from "./modals/modal-backdrop";
import ModalBody from "./modals/ModalBody";
import ModalButton from "./buttons/ModalButton";
import {
  BaseModalTitle,
  BaseModalDescription,
} from "./modals/confirmation-modals/BaseModal";

export function AnalyticsConsentFormModal() {
  const fetcher = useFetcher({ key: "set-consent" });

  return (
    <ModalBackdrop>
      <fetcher.Form
        method="POST"
        action="/set-consent"
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
      </fetcher.Form>
    </ModalBackdrop>
  );
}
