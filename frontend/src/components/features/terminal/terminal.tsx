import { useTerminal } from "#/hooks/use-terminal";
import "@xterm/xterm/css/xterm.css";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { useCommand } from "#/hooks/query/use-command";
import { useAgent } from "#/hooks/query/use-agent";

interface TerminalProps {
  secrets: string[];
}

function Terminal({ secrets }: TerminalProps) {
  const { commands } = useCommand();
  const { curAgentState } = useAgent();

  // Debug log
  // eslint-disable-next-line no-console
  console.log("[Terminal Debug] Rendering terminal with commands:", {
    commandsLength: commands.length,
    agentState: curAgentState,
  });

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
