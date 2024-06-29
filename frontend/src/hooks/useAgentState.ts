import { useSelector } from "react-redux";
import { RootState } from "#/store";
import { changeAgentState } from "#/services/agentStateService";
import AgentState from "#/types/AgentState";

export function useAgentState() {
  const curAgentState = useSelector(
    (state: RootState) => state.agent.curAgentState,
  );

  const setAgentState = (newState: AgentState) => {
    changeAgentState(newState);
  };

  return { curAgentState, setAgentState };
}
