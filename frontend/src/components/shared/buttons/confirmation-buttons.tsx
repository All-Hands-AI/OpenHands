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

  // Narrower check for args that include confirmation_state and security_risk
  const hasRiskAndConfirmation = (
    args: unknown,
  ): args is {
    confirmation_state: "awaiting_confirmation" | "confirmed" | "rejected";
    security_risk: ActionSecurityRisk;
  } =>
    typeof args === "object" &&
    args !== null &&
    "confirmation_state" in (args as Record<string, unknown>) &&
    "security_risk" in (args as Record<string, unknown>);

  // Helper function to check if risk is high, handling different data types
  const isRiskHigh = (risk: ActionSecurityRisk | string | number): boolean => {
    if (typeof risk === "string") {
      return risk.toLowerCase() === "high";
    }
    return Number(risk) === ActionSecurityRisk.HIGH;
  };

  // Detect if the pending action awaiting confirmation is HIGH risk
  const isHighRisk = (() => {
    for (let i = parsedEvents.length - 1; i >= 0; i -= 1) {
      const ev = parsedEvents[i];
      if (
        isOpenHandsAction(ev) &&
        ev.source === "agent" &&
        hasRiskAndConfirmation(ev.args)
      ) {
        if (ev.args.confirmation_state === "awaiting_confirmation") {
          console.log("Found awaiting confirmation event:", ev);
          console.log("Security risk:", ev.args.security_risk, "type:", typeof ev.args.security_risk);
          console.log("ActionSecurityRisk.HIGH:", ActionSecurityRisk.HIGH);
          const isHigh = isRiskHigh(ev.args.security_risk);
          console.log("Is high risk:", isHigh);
          return isHigh;
        }
      }
    }
    return false;
  })();

  return (
    <div className="flex justify-between items-center pt-4">
      <div className="flex flex-col gap-2">
        {isHighRisk && (
          <div className="bg-red-500/10 border border-red-500 text-red-500 rounded px-2 py-1 w-fit flex items-center gap-2">
            <span role="img" aria-label="warning">
              🚨
            </span>
            <span>{t(I18nKey.CHAT_INTERFACE$HIGH_RISK_WARNING)}</span>
          </div>
        )}
        <p>{t(I18nKey.CHAT_INTERFACE$USER_ASK_CONFIRMATION)}</p>
      </div>
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
