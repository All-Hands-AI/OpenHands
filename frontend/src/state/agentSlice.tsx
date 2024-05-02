import { createSlice } from "@reduxjs/toolkit";
import AgentState from "#/types/AgentState";

export const agentSlice = createSlice({
  name: "agent",
  initialState: {
    curAgentState: AgentState.LOADING,
  },
  reducers: {
    changeAgentState: (state, action) => {
      state.curAgentState = action.payload;
    },
  },
});

export const { changeAgentState } = agentSlice.actions;

export default agentSlice.reducer;
