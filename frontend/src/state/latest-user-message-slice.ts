import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import {ActionMessage} from "#/types/message";

export const latestUserMessageSlice = createSlice({
  name: "status",
  initialState: {
    latestUserMessage: null,
  },
  reducers: {
    setLatestUserMessage: (state, action: PayloadAction<ActionMessage>) => {
      state.latestUserMessage = action.payload;
    },
  },
});

export const { setLatestUserMessage } = latestUserMessageSlice.actions;

export default latestUserMessageSlice.reducer;
