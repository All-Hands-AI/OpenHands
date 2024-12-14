import { createSlice, PayloadAction } from "@reduxjs/toolkit";

type SliceState = {
  files: string[]; // base64 encoded images
  initialQuery: string | null;
  selectedRepository: string | null;
  importedProjectZip: string | null; // base64 encoded zip
};

const initialState: SliceState = {
  files: [],
  initialQuery: null,
  selectedRepository: null,
  importedProjectZip: null,
};

export const selectedFilesSlice = createSlice({
  name: "initialQuery",
  initialState,
  reducers: {
    addFile(state, action: PayloadAction<string>) {
      state.files.push(action.payload);
    },
    removeFile(state, action: PayloadAction<number>) {
      state.files.splice(action.payload, 1);
    },
    clearFiles(state) {
      state.files = [];
    },
    setInitialQuery(state, action: PayloadAction<string>) {
      state.initialQuery = action.payload;
    },
    clearInitialQuery(state) {
      state.initialQuery = null;
    },
    setSelectedRepository(state, action: PayloadAction<string | null>) {
      state.selectedRepository = action.payload;
    },
    clearSelectedRepository(state) {
      state.selectedRepository = null;
    },
    setImportedProjectZip(state, action: PayloadAction<string | null>) {
      state.importedProjectZip = action.payload;
    },
  },
});

export const {
  addFile,
  removeFile,
  clearFiles,
  setInitialQuery,
  clearInitialQuery,
  setSelectedRepository,
  clearSelectedRepository,
  setImportedProjectZip,
} = selectedFilesSlice.actions;
export default selectedFilesSlice.reducer;
