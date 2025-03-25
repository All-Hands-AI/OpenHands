import { useSelector } from "react-redux";
import { RootState } from "#/store";
import { useAgentState } from "#/hooks/query/use-agent-state";
import { useTerminal } from "#/hooks/use-terminal";
import "@xterm/xterm/css/xterm.css";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";

interface TerminalProps {
  secrets: string[];
}

function Terminal({ secrets }: TerminalProps) {
  const { commands } = useSelector((state: RootState) => state.cmd);
  const curAgentState = useAgentState();

  const ref = useTerminal({
    commands,
    secrets,
    disabled: RUNTIME_INACTIVE_STATES.includes(curAgentState),
  });

  return (
    <div className="h-full p-2 min-h-0">
      <div ref={ref} className="h-full w-full" />
    </div>
  );
}

export default Terminal;
