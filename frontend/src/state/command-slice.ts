import { createSlice, PayloadAction } from "@reduxjs/toolkit";

export type Command = {
  content: string;
  isPartial?: boolean; // true if the content is partial output
  type: "input" | "output";
};

// Helper function to compare commands
const areCommandsEqual = (cmd1: Command, cmd2: Command): boolean =>
  cmd1.content === cmd2.content &&
  cmd1.type === cmd2.type &&
  cmd1.isPartial === cmd2.isPartial;

const initialCommands: Command[] = [];

export const commandSlice = createSlice({
  name: "command",
  initialState: {
    commands: initialCommands,
  },
  reducers: {
    appendInput: (state, action: PayloadAction<string>) => {
      state.commands.push({ content: action.payload, type: "input" });
    },
    appendOutput: (
      state,
      action: PayloadAction<{ content: string; isPartial?: boolean }>,
    ) => {
      const { content, isPartial } = action.payload;
      const newCommand: Command = {
        content,
        isPartial: isPartial ?? false,
        type: "output",
      };

      // Check if current command is the same as the last command
      const lastCommand = state.commands[state.commands.length - 1];
      if (areCommandsEqual(lastCommand, newCommand)) return;

      state.commands.push(newCommand);
    },
    clearTerminal: (state) => {
      state.commands = [];
    },
  },
});

export const { appendInput, appendOutput, clearTerminal } =
  commandSlice.actions;

export default commandSlice.reducer;
