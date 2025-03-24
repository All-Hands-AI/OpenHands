import { useQuery, useQueryClient } from "@tanstack/react-query";
import { QueryKeys } from "./query-keys";
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
 * Hook to access and manipulate state data
 */
export function useCommand() {
  const queryClient = useQueryClient();
  const queryClient = useQueryClient();
  const getInitialCommandState = (): CommandState => {
    // If we already have data in React Query, use that
    const existingData = queryClient.getQueryData<CommandState>(QueryKeys.command);
    if (existingData) return existingData;
        return initialCommand;
    return initialCommand;
  };
  // Query for command state
  const query = useQuery({
    queryKey: QueryKeys.command,
    queryFn: () => {
      // First check if we already have data in the query cache
      const existingData = queryClient.getQueryData<CommandState>(QueryKeys.command);
      if (existingData) return existingData;
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
      queryClient.getQueryData<CommandState>(QueryKeys.command) || initialCommand;
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
    queryClient.setQueryData<CommandState>(QueryKeys.command, newState);
  };
  // Function to append output (synchronous)
  const appendOutput = (content: string) => {
    // Get current state
    const previousState =
      queryClient.getQueryData<CommandState>(QueryKeys.command) || initialCommand;
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
    queryClient.setQueryData<CommandState>(QueryKeys.command, newState);
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
    queryClient.setQueryData<CommandState>(QueryKeys.command, newState);
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
