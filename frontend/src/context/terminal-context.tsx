import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useMemo,
} from "react";
import { Command } from "#/state/command-slice";

// Context type definition
type TerminalContextType = {
  commands: Command[];
  appendInput: (content: string) => void;
  appendOutput: (content: string) => void;
  clearTerminal: () => void;
};

// Create context with default values
const TerminalContext = createContext<TerminalContextType>({
  commands: [],
  appendInput: () => {},
  appendOutput: () => {},
  clearTerminal: () => {},
});

// Provider component
export function TerminalProvider({ children }: { children: React.ReactNode }) {
  const [commands, setCommands] = useState<Command[]>([]);

  const appendInput = useCallback((content: string) => {
    setCommands((prevCommands) => [
      ...prevCommands,
      { content, type: "input" },
    ]);
  }, []);

  const appendOutput = useCallback((content: string) => {
    setCommands((prevCommands) => [
      ...prevCommands,
      { content, type: "output" },
    ]);
  }, []);

  const clearTerminal = useCallback(() => {
    setCommands([]);
  }, []);

  // Register the functions with the terminal service
  React.useEffect(() => {
    import("#/services/context-services/terminal-service").then(
      ({ registerTerminalFunctions }) => {
        registerTerminalFunctions({
          appendInput,
          appendOutput,
          clearTerminal,
          getCommands: () => commands,
        });
      },
    );
  }, [appendInput, appendOutput, clearTerminal, commands]);

  // Create a memoized context value to prevent unnecessary re-renders
  const contextValue = useMemo(
    () => ({
      commands,
      appendInput,
      appendOutput,
      clearTerminal,
    }),
    [commands, appendInput, appendOutput, clearTerminal],
  );

  return (
    <TerminalContext.Provider value={contextValue}>
      {children}
    </TerminalContext.Provider>
  );
}

// Custom hook to use the terminal context
export function useTerminalContext() {
  const context = useContext(TerminalContext);

  if (context === undefined) {
    throw new Error(
      "useTerminalContext must be used within a TerminalProvider",
    );
  }

  return context;
}
