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
