import { createSlice } from "@reduxjs/toolkit";

export const conversationSlice = createSlice({
  name: "conversation",
  initialState: {
    isRightPanelShown: true as boolean,
    shouldStopConversation: false as boolean,
    shouldStartConversation: false as boolean,
    messageToSend: null as string | null,
  },
  reducers: {
    setIsRightPanelShown: (state, action) => {
      state.isRightPanelShown = action.payload;
    },
    setShouldStopConversation: (state, action) => {
      state.shouldStopConversation = action.payload;
    },
    setShouldStartConversation: (state, action) => {
      state.shouldStartConversation = action.payload;
    },
    setMessageToSend: (state, action) => {
      state.messageToSend = action.payload;
    },
  },
});

export const {
  setIsRightPanelShown,
  setShouldStopConversation,
  setShouldStartConversation,
  setMessageToSend,
} = conversationSlice.actions;

export default conversationSlice.reducer;
