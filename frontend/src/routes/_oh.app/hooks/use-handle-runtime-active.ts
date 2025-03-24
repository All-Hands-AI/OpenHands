import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { useAgentState } from "#/hooks/query/use-agent-state";

export const useHandleRuntimeActive = () => {
  const { curAgentState } = useAgentState();

  const runtimeActive = !RUNTIME_INACTIVE_STATES.includes(curAgentState);

  return { runtimeActive };
};
