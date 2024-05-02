import { createSlice } from "@reduxjs/toolkit";
import AgentTaskState from "#/types/AgentTaskState";
import { setInitialized } from "./taskSlice";

export const agentSlice = createSlice({
  name: "agent",
  initialState: {
    curTaskState: AgentTaskState.INIT,
  },
  reducers: {
    changeAgentState: (state, action) => {
      console.log('state change', action.payload);
      state.curTaskState = action.payload;
      if (action.payload === AgentTaskState.INIT) {
        console.log('setInitialized');
        setInitialized();
      }
    },
  },
});

export const { changeAgentState } = agentSlice.actions;

export default agentSlice.reducer;
