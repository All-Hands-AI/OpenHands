import { createSlice } from "@reduxjs/toolkit";

export const statusSlice = createSlice({
  name: "status",
  initialState: {
    curStatusMessage: "",
  },
  reducers: {
    setCurStatusMessage: (state, action) => {
      state.curStatusMessage = action.payload;
    },
  },
});

export const { setCurStatusMessage } = statusSlice.actions;

export default statusSlice.reducer;
