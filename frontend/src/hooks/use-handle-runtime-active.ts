import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { useExecutionState } from "#/hooks/use-execution-state";

export const useHandleRuntimeActive = () => {
  const { curAgentState } = useExecutionState();

  const runtimeActive = !RUNTIME_INACTIVE_STATES.includes(curAgentState);

  return { runtimeActive };
};
