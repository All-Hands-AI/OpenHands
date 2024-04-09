import { createSlice } from "@reduxjs/toolkit";
import i18next from "i18next";
import { ArgConfigType } from "../types/ConfigType";

export const settingsSlice = createSlice({
  name: "settings",
  initialState: {
    ALL_SETTINGS: localStorage.getItem("ALL_SETTINGS") || "",
    [ArgConfigType.LLM_MODEL]:
      localStorage.getItem(ArgConfigType.LLM_MODEL) || "",
    [ArgConfigType.AGENT]: localStorage.getItem(ArgConfigType.AGENT) || "",
    [ArgConfigType.WORKSPACE_DIR]:
      localStorage.getItem(ArgConfigType.WORKSPACE_DIR) || "",
    [ArgConfigType.LANGUAGE]:
      localStorage.getItem(ArgConfigType.LANGUAGE) || "en",
  } as { [key: string]: string },
  reducers: {
    setByKey: (state, action) => {
      const { key, value } = action.payload;
      state[key] = value;
      console.log("setByKey", key, value);
      localStorage.setItem(key, value);
      // language is a special case for now.
      if (key === ArgConfigType.LANGUAGE) {
        i18next.changeLanguage(value);
      }
    },
    setAllSettings: (state, action) => {
      state.ALL_SETTINGS = action.payload;
      localStorage.setItem("ALL_SETTINGS", action.payload);
    },
  },
});

export const { setByKey, setAllSettings } = settingsSlice.actions;

export default settingsSlice.reducer;
