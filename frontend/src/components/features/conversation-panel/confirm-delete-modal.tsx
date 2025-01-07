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
        <BaseModalTitle title="Are you sure you want to delete this project?" />
        <BaseModalDescription description="All data associated with this project will be lost." />
        <div className="flex flex-col sm:flex-row gap-3 w-full">
          <ModalButton
            onClick={onCancel}
            className="bg-neutral-500 hover:bg-neutral-600 flex-1 font-bold"
            text="Cancel"
          />
          <ModalButton
            onClick={onConfirm}
            className="bg-danger hover:bg-danger/90 flex-1 font-bold"
            data-testid="confirm-delete-button"
            text="Delete"
          />
        </div>
      </ModalBody>
    </ModalBackdrop>
  );
}
