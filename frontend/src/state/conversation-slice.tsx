import { createSlice } from "@reduxjs/toolkit";

export const conversationSlice = createSlice({
  name: "conversation",
  initialState: {
    isRightPanelShown: true as boolean,
    shouldShownAgentLoading: false as boolean,
  },
  reducers: {
    setIsRightPanelShown: (state, action) => {
      state.isRightPanelShown = action.payload;
    },
    setShouldShownAgentLoading: (state, action) => {
      state.shouldShownAgentLoading = action.payload;
    },
  },
});

export const { setIsRightPanelShown, setShouldShownAgentLoading } =
  conversationSlice.actions;

export default conversationSlice.reducer;
