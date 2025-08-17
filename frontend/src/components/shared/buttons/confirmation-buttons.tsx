import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { AgentState } from "#/types/agent-state";
import { generateAgentStateChangeEvent } from "#/services/agent-state-service";
import { useWsClient } from "#/context/ws-client-provider";
import { ActionTooltip } from "../action-tooltip";
import { isOpenHandsAction } from "#/types/core/guards";
import { ActionSafetyRisk } from "#/state/security-analyzer-slice";

export function ConfirmationButtons() {
  const { t } = useTranslation();
  const { send, parsedEvents } = useWsClient();

  const handleStateChange = (state: AgentState) => {
    const event = generateAgentStateChangeEvent(state);
    send(event);
  };

  // Narrower check for args that include confirmation_state and safety_risk
  const hasRiskAndConfirmation = (
    args: unknown,
  ): args is {
    confirmation_state: "awaiting_confirmation" | "confirmed" | "rejected";
    safety_risk: ActionSafetyRisk;
  } =>
    typeof args === "object" &&
    args !== null &&
    "confirmation_state" in (args as Record<string, unknown>) &&
    "safety_risk" in (args as Record<string, unknown>);

  // Helper function to check if risk is high, handling different data types
  const isRiskHigh = (risk: ActionSafetyRisk | string | number): boolean => {
    if (typeof risk === "string") {
      return risk.toLowerCase() === "high";
    }
    return Number(risk) === ActionSafetyRisk.HIGH;
  };

  // Detect if there's a pending action awaiting confirmation and its risk level
  // Show confirmation messages until a new action starts or completes
  const confirmationState = (() => {
    let awaitingConfirmation = null;
    let mostRecentConfirmed = null;
    let mostRecentRejected = null;
    let hasSubsequentAction = false;
    
    for (let i = parsedEvents.length - 1; i >= 0; i -= 1) {
      const ev = parsedEvents[i];
      
      if (
        isOpenHandsAction(ev) &&
        ev.source === "agent" &&
        hasRiskAndConfirmation(ev.args)
      ) {
        const state = ev.args.confirmation_state;
        const isHighRisk = isRiskHigh(ev.args.safety_risk);
        
        // If we find an awaiting confirmation, return it immediately
        if (state === "awaiting_confirmation") {
          awaitingConfirmation = { state, isHighRisk };
          break;
        }
        
        // Store the most recent confirmed/rejected states
        if (state === "confirmed" && !mostRecentConfirmed) {
          mostRecentConfirmed = { state, isHighRisk };
        }
        if (state === "rejected" && !mostRecentRejected) {
          mostRecentRejected = { state, isHighRisk };
        }
      }
      
      // Check if there's a subsequent action after a confirmed/rejected action
      if (
        (mostRecentConfirmed || mostRecentRejected) &&
        isOpenHandsAction(ev) &&
        ev.source === "agent" &&
        !hasRiskAndConfirmation(ev.args)
      ) {
        hasSubsequentAction = true;
      }
    }
    
    // Priority: awaiting confirmation > recent confirmed/rejected (if no subsequent action)
    if (awaitingConfirmation) {
      return awaitingConfirmation;
    }
    
    if (!hasSubsequentAction && (mostRecentConfirmed || mostRecentRejected)) {
      return mostRecentConfirmed || mostRecentRejected;
    }
    
    return { state: null, isHighRisk: false };
  })();

  const isAwaitingConfirmation = confirmationState.state === "awaiting_confirmation";
  const isHighRisk = isAwaitingConfirmation && confirmationState.isHighRisk;
  const wasConfirmed = confirmationState.state === "confirmed";
  const wasRejected = confirmationState.state === "rejected";

  // Don't render anything if there's no confirmation state
  if (!confirmationState.state) {
    return null;
  }

  // Show confirmation message if action was confirmed
  if (wasConfirmed) {
    return (
      <div className="flex flex-col gap-3 pt-4">
        <div className="bg-gradient-to-r from-green-500/15 to-emerald-500/15 border-2 border-green-400/60 text-green-400 rounded-lg px-4 py-3 w-full flex items-center gap-3 shadow-lg backdrop-blur-sm">
          <div className="flex-shrink-0 w-6 h-6 bg-green-500/20 rounded-full flex items-center justify-center">
            <span role="img" aria-label="confirmed" className="text-lg">
              ✅
            </span>
          </div>
          <span className="font-medium text-sm leading-relaxed">
            {t(I18nKey.CHAT_INTERFACE$AGENT_ACTION_USER_CONFIRMED_MESSAGE)}
          </span>
        </div>
      </div>
    );
  }

  // Show rejection message if action was rejected
  if (wasRejected) {
    return (
      <div className="flex flex-col gap-3 pt-4">
        <div className="bg-gradient-to-r from-gray-500/15 to-slate-500/15 border-2 border-gray-400/60 text-gray-400 rounded-lg px-4 py-3 w-full flex items-center gap-3 shadow-lg backdrop-blur-sm">
          <div className="flex-shrink-0 w-6 h-6 bg-gray-500/20 rounded-full flex items-center justify-center">
            <span role="img" aria-label="rejected" className="text-lg">
              ❌
            </span>
          </div>
          <span className="font-medium text-sm leading-relaxed">
            {t(I18nKey.CHAT_INTERFACE$AGENT_ACTION_USER_REJECTED_MESSAGE)}
          </span>
        </div>
      </div>
    );
  }

  // Show confirmation dialog if awaiting confirmation
  return (
    <div className="flex flex-col gap-3 pt-4">
      {isHighRisk && (
        <div className="bg-gradient-to-r from-red-500/15 to-orange-500/15 border-2 border-red-400/60 text-red-400 rounded-lg px-4 py-3 w-full flex items-center gap-3 shadow-lg backdrop-blur-sm">
          <div className="flex-shrink-0 w-6 h-6 bg-red-500/20 rounded-full flex items-center justify-center">
            <span role="img" aria-label="warning" className="text-lg">
              ⚠️
            </span>
          </div>
          <span className="font-medium text-sm leading-relaxed">
            {t(I18nKey.CHAT_INTERFACE$HIGH_RISK_WARNING)}
          </span>
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
