import { createSlice } from "@reduxjs/toolkit";

export const conversationSlice = createSlice({
  name: "conversation",
  initialState: {
    isRightPanelShown: true as boolean,
    messageToSend: null as string | null,
  },
  reducers: {
    setIsRightPanelShown: (state, action) => {
      state.isRightPanelShown = action.payload;
    },
    setMessageToSend: (state, action) => {
      state.messageToSend = action.payload;
    },
  },
});

export const { setIsRightPanelShown, setMessageToSend } =
  conversationSlice.actions;

export default conversationSlice.reducer;
