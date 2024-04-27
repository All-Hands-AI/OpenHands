import { createSlice } from "@reduxjs/toolkit";
import { getSettings } from "#/services/settings";

export const initialState = {
  code: "",
  path: "",
  refreshID: 0,
  workspaceFolder: getSettings().WORKSPACE_SUBDIR,
};

export const codeSlice = createSlice({
  name: "code",
  initialState,
  reducers: {
    setCode: (state, action) => {
      state.code = action.payload;
    },
    setActiveFilepath: (state, action) => {
      state.path = action.payload;
    },
    setRefreshID: (state, action) => {
      state.refreshID = action.payload;
    },
    updateWorkspace: (state, action) => {
      state.workspaceFolder = action.payload;
    },
  },
});

export const { setCode, setActiveFilepath, setRefreshID } = codeSlice.actions;

export default codeSlice.reducer;
