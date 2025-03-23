// Define Cell type locally since it was removed from Redux state
export type Cell = {
  content: string;
  type: "input" | "output";
};

// Function types
type AppendJupyterInputFn = (content: string) => void;
type AppendJupyterOutputFn = (content: string) => void;
type ClearJupyterFn = () => void;
type GetCellsFn = () => Cell[];

// Module-level variables to store the actual functions
let appendJupyterInputImpl: AppendJupyterInputFn = () => {};
let appendJupyterOutputImpl: AppendJupyterOutputFn = () => {};
let clearJupyterImpl: ClearJupyterFn = () => {};
let getCellsImpl: GetCellsFn = () => [];

// Register the functions from the context
export function registerJupyterFunctions({
  appendJupyterInput,
  appendJupyterOutput,
  clearJupyter,
  getCells,
}: {
  appendJupyterInput: AppendJupyterInputFn;
  appendJupyterOutput: AppendJupyterOutputFn;
  clearJupyter: ClearJupyterFn;
  getCells: GetCellsFn;
}): void {
  appendJupyterInputImpl = appendJupyterInput;
  appendJupyterOutputImpl = appendJupyterOutput;
  clearJupyterImpl = clearJupyter;
  getCellsImpl = getCells;
}

// Export the service functions
export const JupyterService = {
  appendJupyterInput: (content: string): void => {
    appendJupyterInputImpl(content);
  },

  appendJupyterOutput: (content: string): void => {
    appendJupyterOutputImpl(content);
  },

  clearJupyter: (): void => {
    clearJupyterImpl();
  },

  getCells: (): Cell[] => getCellsImpl(),
};

// Re-export the service functions for convenience
export const {
  appendJupyterInput,
  appendJupyterOutput,
  clearJupyter,
  getCells,
} = JupyterService;
