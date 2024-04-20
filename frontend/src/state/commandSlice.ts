import { createSlice } from "@reduxjs/toolkit";

export type Command = {
  content: string;
  type: "input" | "output";
};

const initialCommands: Command[] = [];

export const commandSlice = createSlice({
  name: "command",
  initialState: {
    commands: initialCommands,
  },
  reducers: {
    appendInput: (state, action) => {
      state.commands.push({ content: action.payload, type: "input" });
    },
    appendOutput: (state, action) => {
      state.commands.push({ content: action.payload, type: "output" });
    },
  },
});

export const { appendInput, appendOutput } = commandSlice.actions;

export default commandSlice.reducer;
