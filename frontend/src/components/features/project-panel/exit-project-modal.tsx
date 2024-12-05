import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import { ModalButton } from "#/components/shared/buttons/modal-button";
import { BaseModalTitle } from "#/components/shared/modals/confirmation-modals/base-modal";

interface ExitProjectModalProps {
  onConfirm: () => void;
  onClose: () => void;
}

export function ExitProjectModal({
  onConfirm,
  onClose,
}: ExitProjectModalProps) {
  return (
    <ModalBackdrop>
      <ModalBody testID="confirm-new-project-modal">
        <BaseModalTitle title="Creating a New Project will replace your active project" />
        <div className="flex w-full gap-2">
          <ModalButton
            text="Confirm"
            onClick={onConfirm}
            className="bg-[#C63143] flex-1"
          />
          <ModalButton
            text="Cancel"
            onClick={onClose}
            className="bg-neutral-700 flex-1"
          />
        </div>
      </ModalBody>
    </ModalBackdrop>
  );
}
