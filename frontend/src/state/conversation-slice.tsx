import { createSlice } from "@reduxjs/toolkit";

export const conversationSlice = createSlice({
  name: "conversation",
  initialState: {
    isRightPanelShown: true as boolean,
    shouldStopConversation: false as boolean,
    shouldStartConversation: false as boolean,
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
  },
});

export const {
  setIsRightPanelShown,
  setShouldStopConversation,
  setShouldStartConversation,
} = conversationSlice.actions;

export default conversationSlice.reducer;
