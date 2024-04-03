import { createSlice } from "@reduxjs/toolkit";

export const settingsSlice = createSlice({
  name: "settings",
  initialState: {
    model: localStorage.getItem("model") || "",
    agent: localStorage.getItem("agent") || "MonologueAgent",
    workspaceDirectory:
      localStorage.getItem("workspaceDirectory") || "./workspace",
  },
  reducers: {
    setModel: (state, action) => {
      state.model = action.payload;
    },
    setAgent: (state, action) => {
      state.agent = action.payload;
    },
    setWorkspaceDirectory: (state, action) => {
      state.workspaceDirectory = action.payload;
    },
  },
});

export const { setModel, setAgent, setWorkspaceDirectory } =
  settingsSlice.actions;

export default settingsSlice.reducer;
