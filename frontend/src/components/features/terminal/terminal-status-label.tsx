import { useSelector } from "react-redux";
import { cn } from "#/utils/utils";
import { AgentState } from "#/types/agent-state";
import { RootState } from "#/store";

export function TerminalStatusLabel() {
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
      Terminal
    </div>
  );
}
