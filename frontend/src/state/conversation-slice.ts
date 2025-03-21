import { createSlice, PayloadAction } from "@reduxjs/toolkit";

export interface ConversationState {
  id: string | null;
  title: string | null;
  status: string | null;
  selectedRepository: string | null;
  createdAt: string | null;
  lastUpdatedAt: string | null;
}

const initialState: ConversationState = {
  id: null,
  title: null,
  status: null,
  selectedRepository: null,
  createdAt: null,
  lastUpdatedAt: null,
};

export const conversationSlice = createSlice({
  name: "conversation",
  initialState,
  reducers: {
    setConversation: (state, action: PayloadAction<Partial<ConversationState>>) => {
      return { ...state, ...action.payload };
    },
    setConversationTitle: (state, action: PayloadAction<string>) => {
      state.title = action.payload;
    },
    clearConversation: () => initialState,
  },
});

export const { setConversation, setConversationTitle, clearConversation } = conversationSlice.actions;

export default conversationSlice.reducer;