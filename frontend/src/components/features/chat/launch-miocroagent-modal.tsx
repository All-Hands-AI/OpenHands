import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import { BrandButton } from "../settings/brand-button";
import { SettingsInput } from "../settings/settings-input";

interface LaunchMicroagentModalProps {
  onClose: () => void;
  onLaunch: () => void;
}

export function LaunchMicroagentModal({
  onClose,
  onLaunch,
}: LaunchMicroagentModalProps) {
  const formAction = (formData: FormData) => {
    console.log(Object.fromEntries(formData.entries()));
  };

  return (
    <ModalBackdrop>
      <ModalBody>
        <form
          data-testid="launch-microagent-modal"
          action={formAction}
          className="flex flex-col gap-6"
        >
          <SettingsInput
            type="text"
            testId="description-input"
            name="description-input"
            label="What would you like to add to the Microagent?"
          />

          <SettingsInput
            type="text"
            testId="name-input"
            name="name-input"
            label="Name"
            placeholder="Microagent name"
          />

          <SettingsInput
            type="text"
            testId="target-input"
            name="target-input"
            label="Where should we put it?"
          />

          <SettingsInput
            type="text"
            testId="trigger-input"
            name="trigger-input"
            label="Add a trigger for the microagent"
            placeholder="Add a trigger word"
          />

          <div className="flex items-center justify-end gap-2">
            <BrandButton type="button" variant="secondary" onClick={onClose}>
              Cancel
            </BrandButton>
            <BrandButton type="submit" variant="primary" onClick={onLaunch}>
              Launch
            </BrandButton>
          </div>
        </form>
      </ModalBody>
    </ModalBackdrop>
  );
}
