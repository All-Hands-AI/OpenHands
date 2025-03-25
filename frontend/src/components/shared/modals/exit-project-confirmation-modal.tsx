import { useEndSession } from "#/hooks/use-end-session";
import { AgentState } from "#/types/agent-state";
import { DangerModal } from "./confirmation-modals/danger-modal";
import { ModalBackdrop } from "./modal-backdrop";
import { useAgentState } from "#/hooks/state/use-agent-state";

interface ExitProjectConfirmationModalProps {
  onClose: () => void;
}

export function ExitProjectConfirmationModal({
  onClose,
}: ExitProjectConfirmationModalProps) {
  const { setAgentState } = useAgentState();
  const endSession = useEndSession();

  const handleEndSession = () => {
    onClose();
    setAgentState(AgentState.LOADING);
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
