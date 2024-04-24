import { createSlice } from "@reduxjs/toolkit";
import AgentTaskState from "#/types/AgentTaskState";

export const agentSlice = createSlice({
  name: "agent",
  initialState: {
    curTaskState: AgentTaskState.INIT,
  },
  reducers: {
    changeTaskState: (state, action) => {
      state.curTaskState = action.payload;
    },
  },
});

export const { changeTaskState } = agentSlice.actions;

export default agentSlice.reducer;
