import { useQueryClient } from "@tanstack/react-query";
import React from "react";
import { AgentState } from "#/types/agent-state";

const AGENT_STATE_KEY = ["_STATE", "agent"];

export const useAgentState = () => {
  const queryClient = useQueryClient();

  const setAgentState = React.useCallback(
    (status: AgentState) => {
      queryClient.setQueryData<AgentState>(AGENT_STATE_KEY, status);
    },
    [queryClient],
  );

  const agentState =
    queryClient.getQueryData<AgentState>(AGENT_STATE_KEY) || AgentState.LOADING;

  return { agentState, setAgentState };
};
