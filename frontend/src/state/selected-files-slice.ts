import { createSlice, PayloadAction } from "@reduxjs/toolkit";

type SliceState = { files: string[] }; // base64 encoded images

const initialState: SliceState = {
  files: [],
};

export const selectedFilesSlice = createSlice({
  name: "selectedFiles",
  initialState,
  reducers: {
    addFile(state, action: PayloadAction<string>) {
      state.files.push(action.payload);
    },
    removeFile(state, action: PayloadAction<string>) {
      state.files = state.files.filter((file) => file !== action.payload);
    },
    clearFiles(state) {
      state.files = [];
    },
  },
});

export const { addFile, removeFile, clearFiles } = selectedFilesSlice.actions;
export default selectedFilesSlice.reducer;
