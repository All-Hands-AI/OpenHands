import { createSlice } from "@reduxjs/toolkit";

export const conversationSlice = createSlice({
  name: "conversation",
  initialState: {
    isRightPanelShown: true as boolean,
  },
  reducers: {
    setIsRightPanelShown: (state, action) => {
      state.isRightPanelShown = action.payload;
    },
  },
});

export const { setIsRightPanelShown } = conversationSlice.actions;

export default conversationSlice.reducer;
