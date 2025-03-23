import { useSelector } from "react-redux";
import { RootState } from "#/store";

import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";

export const useHandleRuntimeActive = () => {
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const runtimeActive = !RUNTIME_INACTIVE_STATES.includes(curAgentState);

  return { runtimeActive };
};
