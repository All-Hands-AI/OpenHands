import { useTranslation } from "react-i18next";
import { cn } from "#/utils/utils";
import { AgentState } from "#/types/agent-state";
import { I18nKey } from "#/i18n/declaration";
import { useAgentState } from "#/hooks/state/use-agent-state";

export function TerminalStatusLabel() {
  const { t } = useTranslation();
  const { agentState } = useAgentState();

  return (
    <div className="flex items-center gap-2">
      <div
        className={cn(
          "w-2 h-2 rounded-full",
          agentState === AgentState.LOADING || agentState === AgentState.STOPPED
            ? "bg-red-500 animate-pulse"
            : "bg-green-500",
        )}
      />
      {t(I18nKey.WORKSPACE$TERMINAL_TAB_LABEL)}
    </div>
  );
}
