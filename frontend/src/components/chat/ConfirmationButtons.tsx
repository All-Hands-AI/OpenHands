import { Tooltip } from "@nextui-org/react";
import { useTranslation } from "react-i18next";
import ConfirmIcon from "#/assets/confirm";
import RejectIcon from "#/assets/reject";
import { I18nKey } from "#/i18n/declaration";
import AgentState from "#/types/AgentState";
import { generateAgentStateChangeEvent } from "#/services/agentStateService";
import { useSocket } from "#/context/socket";

interface ActionTooltipProps {
  type: "confirm" | "reject";
  onClick: () => void;
}

function ActionTooltip({ type, onClick }: ActionTooltipProps) {
  const { t } = useTranslation();

  const content =
    type === "confirm"
      ? t(I18nKey.CHAT_INTERFACE$USER_CONFIRMED)
      : t(I18nKey.CHAT_INTERFACE$USER_REJECTED);

  return (
    <Tooltip content={content} closeDelay={100}>
      <button
        data-testid={`action-${type}-button`}
        type="button"
        aria-label={type === "confirm" ? "Confirm action" : "Reject action"}
        className="bg-neutral-700 rounded-full p-1 hover:bg-neutral-800"
        onClick={onClick}
      >
        {type === "confirm" ? <ConfirmIcon /> : <RejectIcon />}
      </button>
    </Tooltip>
  );
}

function ConfirmationButtons() {
  const { t } = useTranslation();
  const { send } = useSocket();

  const handleStateChange = (state: AgentState) => {
    const event = generateAgentStateChangeEvent(state);
    send(event);
  };

  return (
    <div className="flex justify-between items-center pt-4">
      <p>{t(I18nKey.CHAT_INTERFACE$USER_ASK_CONFIRMATION)}</p>
      <div className="flex items-center gap-3">
        <ActionTooltip
          type="confirm"
          onClick={() => handleStateChange(AgentState.USER_CONFIRMED)}
        />
        <ActionTooltip
          type="reject"
          onClick={() => handleStateChange(AgentState.USER_REJECTED)}
        />
      </div>
    </div>
  );
}

export default ConfirmationButtons;
