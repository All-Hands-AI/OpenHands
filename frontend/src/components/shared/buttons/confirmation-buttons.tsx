import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { AgentState } from "#/types/agent-state";
import { generateAgentStateChangeEvent } from "#/services/agent-state-service";
import { useWsClient } from "#/context/ws-client-provider";
import { ActionTooltip } from "../action-tooltip";
import { isOpenHandsAction } from "#/types/core/guards";
import { ActionSecurityRisk } from "#/state/security-analyzer-slice";

export function ConfirmationButtons() {
  const { t } = useTranslation();
  const { send, parsedEvents } = useWsClient();

  const handleStateChange = (state: AgentState) => {
    const event = generateAgentStateChangeEvent(state);
    send(event);
  };

  // Find the most recent action awaiting confirmation and check if it's high risk
  const confirmationInfo = (() => {
    for (let i = parsedEvents.length - 1; i >= 0; i -= 1) {
      const ev = parsedEvents[i];
      if (!isOpenHandsAction(ev) || ev.source !== "agent") {
        // eslint-disable-next-line no-continue
        continue;
      }

      const args = ev.args as Record<string, unknown>;
      if (args?.confirmation_state === "awaiting_confirmation") {
        const risk = args?.security_risk;
        const isHighRisk =
          typeof risk === "string"
            ? risk.toLowerCase() === "high"
            : Number(risk) === ActionSecurityRisk.HIGH;

        return { hasConfirmation: true, isHighRisk };
      }
    }
    return { hasConfirmation: false, isHighRisk: false };
  })();

  if (!confirmationInfo.hasConfirmation) {
    return null;
  }

  return (
    <div className="flex flex-col gap-3 pt-4">
      {confirmationInfo.isHighRisk && (
        <div className="bg-red-500/10 border border-red-400/50 text-red-400 rounded-lg px-3 py-2 text-sm">
          {/* eslint-disable-next-line i18next/no-literal-string */}
          <span role="img" aria-label="warning">
            ⚠️
          </span>{" "}
          {t(I18nKey.CHAT_INTERFACE$HIGH_RISK_WARNING)}
        </div>
      )}
      <div className="flex justify-between items-center">
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
    </div>
  );
}
