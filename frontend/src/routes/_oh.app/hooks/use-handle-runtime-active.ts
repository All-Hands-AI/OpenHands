import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { useAgentStateContext } from "#/context/agent-state-context";

export const useHandleRuntimeActive = () => {
  const { curAgentState } = useAgentStateContext();

  const runtimeActive = !RUNTIME_INACTIVE_STATES.includes(curAgentState);

  return { runtimeActive };
};
