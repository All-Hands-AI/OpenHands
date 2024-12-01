import { createSlice } from "@reduxjs/toolkit";

export interface FileState {
  path: string;
  savedContent: string;
  unsavedContent: string;
}

export const initialState = {
  code: "",
  path: "",
  refreshID: 0,
  fileStates: [] as FileState[],
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
    setFileStates: (state, action) => {
      state.fileStates = action.payload;
    },
    addOrUpdateFileState: (state, action) => {
      const { path, unsavedContent, savedContent } = action.payload;
      const newFileStates = state.fileStates.filter(
        (fileState) => fileState.path !== path,
      );
      newFileStates.push({ path, savedContent, unsavedContent });
      state.fileStates = newFileStates;
    },
    removeFileState: (state, action) => {
      const path = action.payload;
      state.fileStates = state.fileStates.filter(
        (fileState) => fileState.path !== path,
      );
    },
  },
});

export const {
  setCode,
  setActiveFilepath,
  setRefreshID,
  addOrUpdateFileState,
  removeFileState,
  setFileStates,
} = codeSlice.actions;

export default codeSlice.reducer;
