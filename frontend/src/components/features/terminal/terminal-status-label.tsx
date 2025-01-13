import { useSelector } from "react-redux";
import { useTranslation } from "react-i18next";
import { cn } from "#/utils/utils";
import { AgentState } from "#/types/agent-state";
import { RootState } from "#/store";
import { I18nKey } from "#/i18n/declaration";

export function TerminalStatusLabel() {
  const { t } = useTranslation();
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  return (
    <div className="flex items-center gap-2">
      <div
        className={cn(
          "w-2 h-2 rounded-full",
          curAgentState === AgentState.LOADING ||
            curAgentState === AgentState.STOPPED
            ? "bg-red-500 animate-pulse"
            : "bg-green-500",
        )}
      />
      {t(I18nKey.WORKSPACE$TERMINAL_TAB_LABEL)}
    </div>
  );
}
