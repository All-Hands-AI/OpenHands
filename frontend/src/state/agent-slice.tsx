import { createSlice } from "@reduxjs/toolkit";
import { AgentState } from "#/types/agent-state";

export const agentSlice = createSlice({
  name: "agent",
  initialState: {
    curAgentState: AgentState.LOADING,
  },
  reducers: {
    setCurrentAgentState: (state, action) => {
      state.curAgentState = action.payload;
    },
  },
});

export const { setCurrentAgentState } = agentSlice.actions;

export default agentSlice.reducer;
