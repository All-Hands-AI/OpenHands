import { useSelector } from "react-redux";
import { useTranslation } from "react-i18next";
import { RootState } from "#/store";
import { useTerminal } from "#/hooks/use-terminal";
import "@xterm/xterm/css/xterm.css";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { cn } from "#/utils/utils";
import { I18nKey } from "#/i18n/declaration";
import { WaitingForRuntimeMessage } from "#/components/features/chat/waiting-for-runtime-message";

function Terminal() {
  const { commands } = useSelector((state: RootState) => state.cmd);
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const isRuntimeInactive = RUNTIME_INACTIVE_STATES.includes(curAgentState);

  const { t } = useTranslation();

  const ref = useTerminal({
    commands,
  });

  return (
    <div className="h-full flex flex-col rounded-xl">
      <div className="flex flex-row items-center justify-between border-b border-[#474A54] py-2 px-3">
        <span className="text-xs font-medium text-white">
          {t(I18nKey.COMMON$TERMINAL)}
        </span>
      </div>

      {isRuntimeInactive && <WaitingForRuntimeMessage className="pt-16" />}

      <div className="flex-1 min-h-0 p-4">
        <div
          ref={ref}
          className={cn(
            "w-full h-full",
            isRuntimeInactive ? "p-0 w-0 h-0 opacity-0 overflow-hidden" : "",
          )}
        />
      </div>
    </div>
  );
}

export default Terminal;
