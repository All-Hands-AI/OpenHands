import { useTerminal } from "#/hooks/use-terminal";
import { RootState } from "#/store";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import "@xterm/xterm/css/xterm.css";
import { useSelector } from "react-redux";

interface TerminalProps {
  secrets: string[];
}

function Terminal({ secrets }: TerminalProps) {
  const { commands } = useSelector((state: RootState) => state.cmd);
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const ref = useTerminal({
    commands,
    secrets,
    disabled: RUNTIME_INACTIVE_STATES.includes(curAgentState),
  });

  return (
    <div className="h-full p-2 min-h-0 ">
      <div ref={ref} className="h-full w-full bg-gray-300" />
    </div>
  );
}

export default Terminal;
