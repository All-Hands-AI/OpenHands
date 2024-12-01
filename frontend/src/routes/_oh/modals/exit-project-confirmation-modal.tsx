import { useDispatch } from "react-redux";
import { DangerModal } from "#/components/modals/confirmation-modals/danger-modal";
import { ModalBackdrop } from "#/components/modals/modal-backdrop";
import { useEndSession } from "#/hooks/use-end-session";
import { setCurrentAgentState } from "#/state/agent-slice";
import AgentState from "#/types/agent-state";

interface ExitProjectConfirmationModalProps {
  onClose: () => void;
}

export function ExitProjectConfirmationModal({
  onClose,
}: ExitProjectConfirmationModalProps) {
  const dispatch = useDispatch();
  const endSession = useEndSession();

  const handleEndSession = () => {
    onClose();
    dispatch(setCurrentAgentState(AgentState.LOADING));
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
