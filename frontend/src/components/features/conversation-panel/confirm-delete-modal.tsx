import { ModalButton } from "#/components/shared/buttons/modal-button";
import {
  BaseModalDescription,
  BaseModalTitle,
} from "#/components/shared/modals/confirmation-modals/base-modal";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";

interface ConfirmDeleteModalProps {
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDeleteModal({
  onConfirm,
  onCancel,
}: ConfirmDeleteModalProps) {
  return (
    <ModalBackdrop>
      <ModalBody className="items-start">
        <div className="flex flex-col gap-2">
          <BaseModalTitle title="Are you sure you want to delete this project?" />
          <BaseModalDescription description="All data associated with this project will be lost." />
        </div>
        <div className="flex flex-col gap-2 w-full">
          <ModalButton
            onClick={onConfirm}
            className="bg-danger font-bold"
            text="Confirm"
          />
          <ModalButton
            onClick={onCancel}
            className="bg-neutral-500 font-bold"
            text="Cancel"
          />
        </div>
      </ModalBody>
    </ModalBackdrop>
  );
}
