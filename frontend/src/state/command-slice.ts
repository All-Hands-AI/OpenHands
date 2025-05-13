import { createSlice, PayloadAction } from "@reduxjs/toolkit";

export type Command = {
  content: string;
  isPartial?: boolean; // true if the content is partial output
  type: "input" | "output";
};

const initialCommands: Command[] = [];

export const commandSlice = createSlice({
  name: "command",
  initialState: {
    commands: initialCommands,
  },
  reducers: {
    appendInput: (state, action: PayloadAction<string>) => {
      state.commands.push({
        content: action.payload,
        isPartial: false,
        type: "input",
      });
    },
    appendOutput: (
      state,
      action: PayloadAction<{ content: string; isPartial?: boolean }>,
    ) => {
      const { content, isPartial } = action.payload;
      state.commands.push({ content, isPartial, type: "output" });
    },
    clearTerminal: (state) => {
      state.commands = [];
    },
  },
});

export const { appendInput, appendOutput, clearTerminal } =
  commandSlice.actions;

export default commandSlice.reducer;
