import { useDispatch } from "react-redux";
import { useTranslation } from "react-i18next";
import { useEndSession } from "#/hooks/use-end-session";
import { setCurrentAgentState } from "#/state/agent-slice";
import { AgentState } from "#/types/agent-state";
import { DangerModal } from "./confirmation-modals/danger-modal";
import { ModalBackdrop } from "./modal-backdrop";
import { I18nKey } from "#/i18n/declaration";

interface ExitProjectConfirmationModalProps {
  onClose: () => void;
}

export function ExitProjectConfirmationModal({
  onClose,
}: ExitProjectConfirmationModalProps) {
  const { t } = useTranslation();
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
        title={t(I18nKey.EXIT_PROJECT$CONFIRM)}
        description={t(I18nKey.EXIT_PROJECT$WARNING)}
        buttons={{
          danger: {
            text: t(I18nKey.EXIT_PROJECT$TITLE),
            onClick: handleEndSession,
          },
          cancel: {
            text: t(I18nKey.BUTTON$CANCEL),
            onClick: onClose,
          },
        }}
      />
    </ModalBackdrop>
  );
}
