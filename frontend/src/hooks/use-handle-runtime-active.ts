import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { useAgentStore } from "#/stores/agent-store";

export const useHandleRuntimeActive = () => {
  const { curAgentState } = useAgentStore();

  const runtimeActive = !RUNTIME_INACTIVE_STATES.includes(curAgentState);

  return { runtimeActive };
};
