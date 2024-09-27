import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { StatusMessage } from "#/types/Message";

const initialStatusMessage: StatusMessage = {
  status: "",
  is_error: false,
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
