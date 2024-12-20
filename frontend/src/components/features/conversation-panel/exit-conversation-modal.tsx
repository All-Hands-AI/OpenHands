import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import { ModalButton } from "#/components/shared/buttons/modal-button";
import { BaseModalTitle } from "#/components/shared/modals/confirmation-modals/base-modal";

interface ExitConversationModalProps {
  onConfirm: () => void;
  onClose: () => void;
}

export function ExitConversationModal({
  onConfirm,
  onClose,
}: ExitConversationModalProps) {
  return (
    <ModalBackdrop>
      <ModalBody testID="confirm-new-conversation-modal">
        <BaseModalTitle title="Creating a new conversation will replace your active conversation" />
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
