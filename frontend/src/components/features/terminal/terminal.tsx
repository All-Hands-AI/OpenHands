import { useSelector } from "react-redux";
import { useTranslation } from "react-i18next";
import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { RootState } from "#/store";
import { useTerminal } from "#/hooks/use-terminal";
import "@xterm/xterm/css/xterm.css";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { cn } from "#/utils/utils";
import CloseIcon from "#/icons/close.svg?react";
import { I18nKey } from "#/i18n/declaration";
import { useConversationTabs } from "../conversation/conversation-tabs/use-conversation-tabs";

function Terminal() {
  // eslint-disable-next-line @typescript-eslint/naming-convention, @typescript-eslint/no-unused-vars
  const [_, { onTerminalChange }] = useConversationTabs();
  const { commands } = useSelector((state: RootState) => state.cmd);
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const isRuntimeInactive = RUNTIME_INACTIVE_STATES.includes(curAgentState);
  const [expanded, setExpanded] = useState(true);
  const { t } = useTranslation();

  const ref = useTerminal({
    commands,
  });

  return (
    <div
      className={cn(
        "border-1 border-[#474A54] rounded-xl",
        "bg-[#282A2E]",
        expanded && "h-80",
      )}
    >
      <div
        className={cn(
          "flex flex-row items-center justify-between",
          expanded && "border-b-1 border-[#474A54]",
          "py-2 px-3",
        )}
      >
        <span className="text-xs font-medium text-white">
          {t(I18nKey.TERMINAL$CONSOLE)}
        </span>

        <div className={cn("flex flex-row items-center gap-x-2")}>
          <button
            className="cursor-pointer"
            type="button"
            onClick={() => setExpanded((value) => !value)}
          >
            <ChevronDown
              className={cn(
                "transform transition-transform duration-300",
                !expanded ? "rotate-180" : "rotate-0",
              )}
              size={18}
            />
          </button>
          <button
            className="cursor-pointer"
            type="button"
            onClick={() => onTerminalChange(false)}
          >
            <CloseIcon />
          </button>
        </div>
      </div>

      {isRuntimeInactive && (
        <div className="w-full flex items-center text-center justify-center text-2xl text-tertiary-light pt-16">
          {t("DIFF_VIEWER$WAITING_FOR_RUNTIME")}
        </div>
      )}

      <div
        ref={ref}
        className={cn(
          isRuntimeInactive || !expanded
            ? "p-0 w-0 h-0 opacity-0 overflow-hidden"
            : "p-4 h-full w-full",
        )}
      />
    </div>
  );
}

export default Terminal;
