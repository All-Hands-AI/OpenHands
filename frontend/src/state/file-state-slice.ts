// DEPRECATED: This file is scheduled for removal as part of the React Query migration.
// It is kept temporarily to maintain backward compatibility until the migration is complete.

import { createSlice, PayloadAction } from "@reduxjs/toolkit";

type SliceState = { changed: Record<string, boolean> }; // Map<path, changed>

const initialState: SliceState = {
  changed: {},
};

export const fileStateSlice = createSlice({
  name: "fileState",
  initialState,
  reducers: {
    setChanged(
      state,
      action: PayloadAction<{ path: string; changed: boolean }>,
    ) {
      const { path, changed } = action.payload;
      state.changed[path] = changed;
    },
  },
});

export const { setChanged } = fileStateSlice.actions;
export default fileStateSlice.reducer;
