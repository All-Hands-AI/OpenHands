import { useSelector } from "react-redux";
import { useTranslation } from "react-i18next";
import { RootState } from "#/store";
import { useTerminal } from "#/hooks/use-terminal";
import "@xterm/xterm/css/xterm.css";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";

function Terminal() {
  const { commands } = useSelector((state: RootState) => state.cmd);
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const isRuntimeInactive = RUNTIME_INACTIVE_STATES.includes(curAgentState);
  const { t } = useTranslation();

  const ref = useTerminal({
    commands,
  });

  return (
    <div className="h-full p-2 min-h-0 flex-grow">
      {isRuntimeInactive && (
        <div className="w-full h-full flex items-center text-center justify-center text-2xl text-tertiary-light">
          {t("DIFF_VIEWER$WAITING_FOR_RUNTIME")}
        </div>
      )}
      <div ref={ref} className="h-full w-full" />
    </div>
  );
}

export default Terminal;
