import { createSlice, PayloadAction } from "@reduxjs/toolkit";

type SliceState = {
  files: string[]; // base64 encoded images
  initialQuery: string | null;
  selectedRepository: string | null;
};

const initialState: SliceState = {
  files: [],
  initialQuery: null,
  selectedRepository: null,
};

export const selectedFilesSlice = createSlice({
  name: "initialQuery",
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
    setInitialQuery(state, action: PayloadAction<string>) {
      state.initialQuery = action.payload;
    },
    setSelectedRepository(state, action: PayloadAction<string | null>) {
      state.selectedRepository = action.payload;
    },
  },
});

export const {
  addFile,
  removeFile,
  clearFiles,
  setInitialQuery,
  setSelectedRepository,
} = selectedFilesSlice.actions;
export default selectedFilesSlice.reducer;
