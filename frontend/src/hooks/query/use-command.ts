import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getQueryReduxBridge } from "#/utils/query-redux-bridge";

export type Command = {
  content: string;
  type: "input" | "output";
};

interface CommandState {
  commands: Command[];
}

// Initial state
const initialCommand: CommandState = {
  commands: [],
};

/**
 * Hook to access and manipulate command data using React Query
 * This replaces the Redux command slice functionality
 */
export function useCommand() {
  const queryClient = useQueryClient();

  // Try to get the bridge, but don't throw if it's not initialized (for tests)
  let bridge: ReturnType<typeof getQueryReduxBridge> | null = null;
  try {
    bridge = getQueryReduxBridge();
  } catch (error) {
    // In tests, we might not have the bridge initialized
    // eslint-disable-next-line no-console
    console.warn(
      "QueryReduxBridge not initialized, using default command state",
    );
  }

  // Get initial state from Redux if this is the first time accessing the data
  const getInitialCommandState = (): CommandState => {
    // If we already have data in React Query, use that
    const existingData = queryClient.getQueryData<CommandState>(["command"]);
    if (existingData) return existingData;

    // Otherwise, get initial data from Redux if bridge is available
    if (bridge) {
      try {
        return bridge.getReduxSliceState<CommandState>("cmd");
      } catch (error) {
        // If we can't get the state from Redux, return the initial state
        return initialCommand;
      }
    }

    // If bridge is not available, return the initial state
    return initialCommand;
  };

  // Query for command state
  const query = useQuery({
    queryKey: ["command"],
    queryFn: () => {
      // First check if we already have data in the query cache
      const existingData = queryClient.getQueryData<CommandState>(["command"]);
      if (existingData) return existingData;

      // Otherwise get from the bridge or use initial state
      return getInitialCommandState();
    },
    initialData: initialCommand, // Use initialCommand directly to ensure it's always defined
    staleTime: Infinity, // We manage updates manually through mutations
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  // Function to append input (synchronous)
  const appendInput = (content: string) => {
    // Get current state
    const previousState =
      queryClient.getQueryData<CommandState>(["command"]) || initialCommand;

    // Update state
    const newState = {
      ...previousState,
      commands: [
        ...previousState.commands,
        { content, type: "input" as const },
      ],
    };

    // Debug log
    // eslint-disable-next-line no-console
    console.log("[Command Debug] Appending input:", { content, newState });

    // Set the state synchronously
    queryClient.setQueryData<CommandState>(["command"], newState);
  };

  // Function to append output (synchronous)
  const appendOutput = (content: string) => {
    // Get current state
    const previousState =
      queryClient.getQueryData<CommandState>(["command"]) || initialCommand;

    // Update state
    const newState = {
      ...previousState,
      commands: [
        ...previousState.commands,
        { content, type: "output" as const },
      ],
    };

    // Debug log
    // eslint-disable-next-line no-console
    console.log("[Command Debug] Appending output:", {
      content,
      commandsLength: newState.commands.length,
    });

    // Set the state synchronously
    queryClient.setQueryData<CommandState>(["command"], newState);
  };

  // Function to clear terminal (synchronous)
  const clearTerminal = () => {
    // Update state
    const newState = {
      commands: [],
    };

    // Debug log
    // eslint-disable-next-line no-console
    console.log("[Command Debug] Clearing terminal");

    // Set the state synchronously
    queryClient.setQueryData<CommandState>(["command"], newState);
  };

  return {
    // State
    commands: query.data?.commands || initialCommand.commands,
    isLoading: query.isLoading,

    // Actions
    appendInput,
    appendOutput,
    clearTerminal,
  };
}
