import { createSlice } from "@reduxjs/toolkit";
import i18next from "i18next";

export const settingsSlice = createSlice({
  name: "settings",
  initialState: {
    model: localStorage.getItem("model") || "gpt-3.5-turbo-1106",
    agent: localStorage.getItem("agent") || "MonologueAgent",
    workspaceDirectory:
      localStorage.getItem("workspaceDirectory") || "./workspace",
    language: localStorage.getItem("language") || "en",
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
    setLanguage: (state, action) => {
      localStorage.setItem("workspaceDirectory", action.payload);
      state.language = action.payload;
      i18next.changeLanguage(action.payload);
    },
  },
});

export const { setModel, setAgent, setWorkspaceDirectory, setLanguage } =
  settingsSlice.actions;

export default settingsSlice.reducer;
