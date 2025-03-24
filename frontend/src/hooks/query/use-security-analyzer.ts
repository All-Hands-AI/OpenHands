import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getQueryReduxBridge } from "#/utils/query-redux-bridge";
import {
  ActionSecurityRisk,
  SecurityAnalyzerLog,
} from "#/types/migrated-types";

/**
 * Hook to access and manipulate security analyzer logs using React Query
 * This replaces the Redux securityAnalyzer slice functionality
 */
export function useSecurityAnalyzer() {
  const queryClient = useQueryClient();

  // Try to get the bridge, but don't throw if it's not initialized (for tests)
  let bridge: ReturnType<typeof getQueryReduxBridge> | null = null;
  try {
    bridge = getQueryReduxBridge();
  } catch (error) {
    // In tests, we might not have the bridge initialized
    console.warn(
      "QueryReduxBridge not initialized, using default security analyzer logs",
    );
  }

  // Get initial state from Redux if this is the first time accessing the data
  const getInitialLogs = (): SecurityAnalyzerLog[] => {
    // If we already have data in React Query, use that
    const existingData = queryClient.getQueryData<SecurityAnalyzerLog[]>([
      "securityAnalyzer",
      "logs",
    ]);
    if (existingData) return existingData;

    // Otherwise, get initial data from Redux if bridge is available
    if (bridge) {
      try {
        return bridge.getReduxSliceState<{ logs: SecurityAnalyzerLog[] }>(
          "securityAnalyzer",
        ).logs;
      } catch (error) {
        // If we can't get the state from Redux, return the initial state
        return [];
      }
    }

    // If bridge is not available, return the initial state
    return [];
  };

  // Query for security analyzer logs
  const query = useQuery({
    queryKey: ["securityAnalyzer", "logs"],
    queryFn: () => getInitialLogs(),
    initialData: getInitialLogs,
    staleTime: Infinity, // We manage updates manually through mutations
  });

  // Mutation to append security analyzer input
  const appendSecurityAnalyzerInputMutation = useMutation({
    mutationFn: (payload: {
      id: number;
      args: {
        command?: string;
        code?: string;
        content?: string;
        security_risk: ActionSecurityRisk;
        confirmation_state?: "awaiting_confirmation" | "confirmed" | "rejected";
      };
      message?: string;
    }) => Promise.resolve(payload),
    onMutate: async (payload) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({
        queryKey: ["securityAnalyzer", "logs"],
      });

      // Get current logs
      const previousLogs =
        queryClient.getQueryData<SecurityAnalyzerLog[]>([
          "securityAnalyzer",
          "logs",
        ]) || [];

      const content =
        payload.args.command ||
        payload.args.code ||
        payload.args.content ||
        payload.message ||
        "";

      const log: SecurityAnalyzerLog = {
        id: payload.id,
        content,
        security_risk: payload.args.security_risk as ActionSecurityRisk,
        confirmation_state: payload.args.confirmation_state,
        confirmed_changed: false,
      };

      // Check if log already exists
      const existingLogIndex = previousLogs.findIndex(
        (stateLog) =>
          stateLog.id === log.id ||
          (stateLog.confirmation_state === "awaiting_confirmation" &&
            stateLog.content === log.content),
      );

      let updatedLogs: SecurityAnalyzerLog[];

      if (existingLogIndex !== -1) {
        // Update existing log
        updatedLogs = [...previousLogs];
        const existingLog = { ...updatedLogs[existingLogIndex] };

        if (existingLog.confirmation_state !== log.confirmation_state) {
          existingLog.confirmation_state = log.confirmation_state;
          existingLog.confirmed_changed = true;
        }

        updatedLogs[existingLogIndex] = existingLog;
      } else {
        // Add new log
        updatedLogs = [...previousLogs, log];
      }

      // Update logs
      queryClient.setQueryData(["securityAnalyzer", "logs"], updatedLogs);

      return { previousLogs };
    },
    onError: (_, __, context) => {
      // Restore previous logs on error
      if (context?.previousLogs) {
        queryClient.setQueryData(
          ["securityAnalyzer", "logs"],
          context.previousLogs,
        );
      }
    },
  });

  return {
    logs: query.data || [],
    isLoading: query.isLoading,
    appendSecurityAnalyzerInput: appendSecurityAnalyzerInputMutation.mutate,
  };
}
