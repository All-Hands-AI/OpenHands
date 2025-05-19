import { useSelector } from "react-redux";
import { useTranslation } from "react-i18next";
import { Switch } from "@heroui/react";
import { useWsClient } from "#/context/ws-client-provider";
import { RootState } from "#/store";
import { cn } from "#/utils/utils";
import {
  generateDelegateToReadOnlyAction,
  generateFinishDelegationAction,
} from "#/services/agent-mode-service";
import { AgentState } from "#/types/agent-state";
import { I18nKey } from "#/i18n/declaration";

export function AgentModeToggle() {
  const { t } = useTranslation();
  const { send } = useWsClient();

  // Get agent type and state from Redux
  const { currentAgentType, curAgentState } = useSelector(
    (state: RootState) => state.agent,
  );

  // Compute if we're in read-only mode
  const isReadOnly = currentAgentType === "ReadOnlyAgent";

  // Check if toggle is disabled (should be disabled during certain agent states)
  const isDisabled = [
    AgentState.LOADING,
    AgentState.INIT,
    AgentState.ERROR,
    AgentState.RATE_LIMITED,
  ].includes(curAgentState);

  const handleToggle = () => {
    if (isReadOnly) {
      // Currently in read-only mode, switch back to execute mode
      send(generateFinishDelegationAction());
    } else {
      // Currently in execute mode, switch to read-only mode
      send(generateDelegateToReadOnlyAction());
    }
  };

  return (
    <div className="flex items-center gap-2">
      <Switch
        isDisabled={isDisabled}
        name="agent-mode"
        isSelected={isReadOnly}
        onValueChange={handleToggle}
        classNames={{
          thumb: cn("bg-white w-3 h-3"),
          wrapper: cn(
            "border border-[#D4D4D4] bg-white px-[6px] w-12 h-6",
            "group-data-[selected=true]:border-transparent",
            isReadOnly
              ? "group-data-[selected=true]:bg-amber-600"
              : "group-data-[selected=true]:bg-blue-600",
          ),
          label: "text-[#A3A3A3] text-xs",
        }}
      >
        <span className="sr-only">{t(I18nKey.AGENT$MODE_TOGGLE_LABEL)}</span>
        <span className="text-sm font-medium ml-2">
          {isReadOnly
            ? t(I18nKey.AGENT$MODE_READ_ONLY)
            : t(I18nKey.AGENT$MODE_EXECUTE)}
        </span>
      </Switch>
    </div>
  );
}
