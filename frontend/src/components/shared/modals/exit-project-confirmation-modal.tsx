import { useEndSession } from "#/hooks/use-end-session";
import { AgentState } from "#/types/agent-state";
import { useAgentState } from "#/hooks/query/use-agent-state";
import { DangerModal } from "./confirmation-modals/danger-modal";
import { ModalBackdrop } from "./modal-backdrop";

interface ExitProjectConfirmationModalProps {
  onClose: () => void;
}

export function ExitProjectConfirmationModal({
  onClose,
}: ExitProjectConfirmationModalProps) {
  const { setCurrentAgentState } = useAgentState();
  const endSession = useEndSession();

  const handleEndSession = () => {
    onClose();
    setCurrentAgentState(AgentState.LOADING);
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
