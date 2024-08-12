import { createSlice } from "@reduxjs/toolkit";

export interface UnsavedEdit {
  path: string;
  content: string;
}

export const initialState = {
  code: "",
  path: "",
  refreshID: 0,
  unsavedEdits: [] as UnsavedEdit[],
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
    addOrUpdateUnsavedEdit: (state, action) => {
      const { path, content } = action.payload;
      const newUnsavedEdits = state.unsavedEdits.filter(
        (unsavedEdit) => unsavedEdit.path !== path,
      );
      newUnsavedEdits.push({ path, content });
      state.unsavedEdits = newUnsavedEdits;
    },
    removeUnsavedEdit: (state, action) => {
      const { path } = action.payload;
      state.unsavedEdits = state.unsavedEdits.filter(
        (unsavedEdit) => unsavedEdit.path !== path,
      );
    },
  },
});

export const {
  setCode,
  setActiveFilepath,
  setRefreshID,
  addOrUpdateUnsavedEdit,
  removeUnsavedEdit,
} = codeSlice.actions;

export default codeSlice.reducer;
