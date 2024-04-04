import { createSlice } from "@reduxjs/toolkit";

export const settingsSlice = createSlice({
  name: "settings",
  initialState: {
    model: localStorage.getItem("model") || "gpt-3.5-turbo-1106",
    agent: localStorage.getItem("agent") || "MonologueAgent",
    workspaceDirectory:
      localStorage.getItem("workspaceDirectory") || "./workspace",
  },
  reducers: {
    setModel: (state, action) => {
      localStorage.setItem("model", action.payload);
      state.model = action.payload;
    },
    setAgent: (state, action) => {
      localStorage.setItem("agent", action.payload);
      state.agent = action.payload;
    },
    setWorkspaceDirectory: (state, action) => {
      localStorage.setItem("workspaceDirectory", action.payload);
      state.workspaceDirectory = action.payload;
    },
  },
});

export const { setModel, setAgent, setWorkspaceDirectory } =
  settingsSlice.actions;

export default settingsSlice.reducer;
