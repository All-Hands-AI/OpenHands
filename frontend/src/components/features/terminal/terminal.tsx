import { useSelector } from "react-redux";
import { useTranslation } from "react-i18next";
import { RootState } from "#/store";
import { useTerminal } from "#/hooks/use-terminal";
import "@xterm/xterm/css/xterm.css";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { cn } from "#/utils/utils";

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
      {isRuntimeInactive && (
        <div className="w-full flex items-center text-center justify-center text-2xl text-tertiary-light pt-16">
          {t("DIFF_VIEWER$WAITING_FOR_RUNTIME")}
        </div>
      )}

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
