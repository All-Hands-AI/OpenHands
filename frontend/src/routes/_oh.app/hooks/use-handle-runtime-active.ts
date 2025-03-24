import { useAgent } from "#/hooks/query/use-agent";

import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";

export const useHandleRuntimeActive = () => {
  const { curAgentState } = useAgent();

  const runtimeActive = !RUNTIME_INACTIVE_STATES.includes(curAgentState);

  return { runtimeActive };
};
