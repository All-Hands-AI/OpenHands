// DEPRECATED: This file is scheduled for removal as part of the React Query migration.
// It is kept temporarily to maintain backward compatibility until the migration is complete.

import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { StatusMessage } from "#/types/message";

const initialStatusMessage: StatusMessage = {
  status_update: true,
  type: "info",
  id: "",
  message: "",
};

export const statusSlice = createSlice({
  name: "status",
  initialState: {
    curStatusMessage: initialStatusMessage,
  },
  reducers: {
    setCurStatusMessage: (state, action: PayloadAction<StatusMessage>) => {
      state.curStatusMessage = action.payload;
    },
  },
});

export const { setCurStatusMessage } = statusSlice.actions;

export default statusSlice.reducer;
