import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { QueryKeys } from "./query-keys";
import { AgentState } from "#/types/agent-state";

interface AgentStateData {
  curAgentState: AgentState;
}

// Initial agent state
const initialAgentState: AgentStateData = {
  curAgentState: AgentState.LOADING,
};

/**
 * Hook to access and manipulate agent state using React Query
 */
export function useAgentState() {
  const queryClient = useQueryClient();
  const agentQueryKey = QueryKeys.agent;

  // Query for agent state
  const query = useQuery({
    queryKey: agentQueryKey,
    queryFn: () => initialAgentState,
    initialData: initialAgentState,
    staleTime: Infinity, // We manage updates manually through mutations
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  // Mutation to set agent state
  const setAgentStateMutation = useMutation({
    mutationFn: (agentState: AgentState) =>
      Promise.resolve({ curAgentState: agentState }),
    onMutate: async (agentState) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({
        queryKey: agentQueryKey,
      });
      
      // Get current agent state
      const previousAgentState = queryClient.getQueryData<AgentStateData>(agentQueryKey);
      
      // Update agent state
      queryClient.setQueryData(agentQueryKey, { curAgentState: agentState });
      
      return { previousAgentState };
    },
    onError: (_, __, context) => {
      // Restore previous agent state on error
      if (context?.previousAgentState) {
        queryClient.setQueryData(agentQueryKey, context.previousAgentState);
      }
    },
  });

  return {
    curAgentState: query.data?.curAgentState || initialAgentState.curAgentState,
    isLoading: query.isLoading,
    setCurrentAgentState: setAgentStateMutation.mutate,
  };
}
