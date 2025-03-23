// No longer need useDispatch since we're using the agent state service
import { useEndSession } from "#/hooks/use-end-session";
import { AgentState } from "#/types/agent-state";
import { updateAgentState } from "#/services/context-services/agent-state-service";
import { DangerModal } from "./confirmation-modals/danger-modal";
import { ModalBackdrop } from "./modal-backdrop";

interface ExitProjectConfirmationModalProps {
  onClose: () => void;
}

export function ExitProjectConfirmationModal({
  onClose,
}: ExitProjectConfirmationModalProps) {
  // No longer need dispatch since we're using the agent state service
  const endSession = useEndSession();

  const handleEndSession = () => {
    onClose();
    updateAgentState(AgentState.LOADING);
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
