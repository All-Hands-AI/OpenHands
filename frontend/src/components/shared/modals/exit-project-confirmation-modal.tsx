import { useEndSession } from "#/hooks/use-end-session";
import { DangerModal } from "./confirmation-modals/danger-modal";
import { ModalBackdrop } from "./modal-backdrop";

interface ExitProjectConfirmationModalProps {
  onClose: () => void;
}

export function ExitProjectConfirmationModal({
  onClose,
}: ExitProjectConfirmationModalProps) {
  const endSession = useEndSession();

  const handleEndSession = () => {
    onClose();
    // Agent state will be updated through WebSocket
    endSession();
  };

  return (
    <ModalBackdrop onClose={onClose}>
      <DangerModal
        title="Are you sure you want to exit?"
        description="You will lose any unsaved information."
        buttons={{
          danger: {
            text: "Exit Project",
            onClick: handleEndSession,
          },
          cancel: {
            text: "Cancel",
            onClick: onClose,
          },
        }}
      />
    </ModalBackdrop>
  );
}
