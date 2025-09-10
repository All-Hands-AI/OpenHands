import { useDispatch, useSelector } from "react-redux";
import { useCallback, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { AgentState } from "#/types/agent-state";
import { generateAgentStateChangeEvent } from "#/services/agent-state-service";
import { useWsClient } from "#/context/ws-client-provider";
import { ActionTooltip } from "../action-tooltip";
import { isOpenHandsAction } from "#/types/core/guards";
import { ActionSecurityRisk } from "#/state/security-analyzer-slice";
import { RiskAlert } from "#/components/shared/risk-alert";
import WarningIcon from "#/icons/u-warning.svg?react";
import { RootState } from "#/store";
import { addSubmittedEventId } from "#/state/event-message-slice";

export function ConfirmationButtons() {
  const submittedEventIds = useSelector(
    (state: RootState) => state.eventMessage.submittedEventIds,
  );

  const dispatch = useDispatch();

  const { t } = useTranslation();

  const { send, parsedEvents } = useWsClient();

  // Find the most recent action awaiting confirmation
  const awaitingAction = parsedEvents
    .slice()
    .reverse()
    .find((ev) => {
      if (!isOpenHandsAction(ev) || ev.source !== "agent") return false;
      const args = ev.args as Record<string, unknown>;
      return args?.confirmation_state === "awaiting_confirmation";
    });

  const handleStateChange = useCallback(
    (state: AgentState) => {
      if (!awaitingAction) {
        return;
      }

      dispatch(addSubmittedEventId(awaitingAction.id));
      send(generateAgentStateChangeEvent(state));
    },
    [send],
  );

  // Handle keyboard shortcuts
  useEffect(() => {
    if (!awaitingAction) {
      return undefined;
    }

    const handleCancelShortcut = (event: KeyboardEvent) => {
      if (event.shiftKey && event.metaKey && event.key === "Backspace") {
        event.preventDefault();
        handleStateChange(AgentState.USER_REJECTED);
      }
    };

    const handleContinueShortcut = (event: KeyboardEvent) => {
      if (event.metaKey && event.key === "Enter") {
        event.preventDefault();
        handleStateChange(AgentState.USER_CONFIRMED);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      // Cancel: Shift+Cmd+Backspace (⇧⌘⌫)
      handleCancelShortcut(event);
      // Continue: Cmd+Enter (⌘↩)
      handleContinueShortcut(event);
    };

    document.addEventListener("keydown", handleKeyDown);

    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [awaitingAction, handleStateChange]);

  if (!awaitingAction || submittedEventIds.includes(awaitingAction.id)) {
    return null;
  }

  const { args } = awaitingAction as { args: Record<string, unknown> };

  const risk = args?.security_risk;

  const isHighRisk =
    typeof risk === "string"
      ? risk.toLowerCase() === "high"
      : Number(risk) === ActionSecurityRisk.HIGH;

  return (
    <div className="flex flex-col gap-2 pt-4">
      {isHighRisk && (
        <RiskAlert
          content={t(I18nKey.CHAT_INTERFACE$HIGH_RISK_WARNING)}
          icon={<WarningIcon width={16} height={16} color="#fff" />}
          severity="high"
          title={t(I18nKey.COMMON$HIGH_RISK)}
        />
      )}
      <div className="flex justify-between items-center">
        <p className="text-sm font-normal text-white">
          {t(I18nKey.CHAT_INTERFACE$USER_ASK_CONFIRMATION)}
        </p>
        <div className="flex items-center gap-3">
          <ActionTooltip
            type="reject"
            onClick={() => handleStateChange(AgentState.USER_REJECTED)}
          />
          <ActionTooltip
            type="confirm"
            onClick={() => handleStateChange(AgentState.USER_CONFIRMED)}
          />
        </div>
      </div>
    </div>
  );
}
