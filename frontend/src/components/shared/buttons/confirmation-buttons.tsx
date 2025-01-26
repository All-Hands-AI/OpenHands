import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { AgentState } from "#/types/agent-state";
import { generateAgentStateChangeEvent } from "#/services/agent-state-service";
import { useWsClient } from "#/context/ws-client-provider";
import { ActionTooltip } from "../action-tooltip";

export function ConfirmationButtons() {
  const { t } = useTranslation();
  const { send } = useWsClient();

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
