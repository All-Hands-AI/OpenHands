// Define Command type locally since it was removed from Redux state
export type Command = {
  content: string;
  type: "input" | "output";
};

// Function types
type AppendInputFn = (content: string) => void;
type AppendOutputFn = (content: string) => void;
type ClearTerminalFn = () => void;
type GetCommandsFn = () => Command[];

// Module-level variables to store the actual functions
let appendInputImpl: AppendInputFn = () => {};
let appendOutputImpl: AppendOutputFn = () => {};
let clearTerminalImpl: ClearTerminalFn = () => {};
let getCommandsImpl: GetCommandsFn = () => [];

// Register the functions from the context
export function registerTerminalFunctions({
  appendInput,
  appendOutput,
  clearTerminal,
  getCommands,
}: {
  appendInput: AppendInputFn;
  appendOutput: AppendOutputFn;
  clearTerminal: ClearTerminalFn;
  getCommands: GetCommandsFn;
}): void {
  appendInputImpl = appendInput;
  appendOutputImpl = appendOutput;
  clearTerminalImpl = clearTerminal;
  getCommandsImpl = getCommands;
}

// Export the service functions
export const TerminalService = {
  appendInput: (content: string): void => {
    appendInputImpl(content);
  },

  appendOutput: (content: string): void => {
    appendOutputImpl(content);
  },

  clearTerminal: (): void => {
    clearTerminalImpl();
  },

  getCommands: (): Command[] => getCommandsImpl(),
};

// Re-export the service functions for convenience
export const { appendInput, appendOutput, clearTerminal, getCommands } =
  TerminalService;
