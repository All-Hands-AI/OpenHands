import { useSelector } from "react-redux";
import { RootState } from "#/store";
import { useTerminal } from "#/hooks/use-terminal";
import "@xterm/xterm/css/xterm.css";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { useAgentState } from "#/hooks/state/use-agent-state";

interface TerminalProps {
  secrets: string[];
}

function Terminal({ secrets }: TerminalProps) {
  const { commands } = useSelector((state: RootState) => state.cmd);
  const { agentState } = useAgentState();

  const ref = useTerminal({
    commands,
    secrets,
    disabled: RUNTIME_INACTIVE_STATES.includes(agentState),
  });

  return (
    <div className="h-full p-2 min-h-0">
      <div ref={ref} className="h-full w-full" />
    </div>
  );
}

export default Terminal;
