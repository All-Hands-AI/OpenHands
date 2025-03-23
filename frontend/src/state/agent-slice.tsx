// DEPRECATED: This file is scheduled for removal as part of the React Query migration.
// It is kept temporarily to maintain backward compatibility until the migration is complete.

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
