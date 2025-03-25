import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { useAgentState } from "#/hooks/state/use-agent-state";

export const useHandleRuntimeActive = () => {
  const { agentState } = useAgentState();
  const runtimeActive = !RUNTIME_INACTIVE_STATES.includes(agentState);

  return { runtimeActive };
};
