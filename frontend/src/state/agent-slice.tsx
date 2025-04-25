import { createSlice } from "@reduxjs/toolkit";
import { AgentState } from "#/types/agent-state";

export const agentSlice = createSlice({
  name: "agent",
  initialState: {
    curAgentState: AgentState.LOADING,
    currentAgentType: "CodeActAgent", // Default agent type
    isDelegated: false, // Track if we're in a delegation
  },
  reducers: {
    setCurrentAgentState: (state, action) => {
      state.curAgentState = action.payload;
    },
    setAgentType: (state, action) => {
      state.currentAgentType = action.payload;
    },
    setDelegationState: (state, action) => {
      state.isDelegated = action.payload;
    },
  },
});

export const { setCurrentAgentState, setAgentType, setDelegationState } =
  agentSlice.actions;

export default agentSlice.reducer;
