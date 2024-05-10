import { createSlice } from "@reduxjs/toolkit";
import { Task, TaskState } from "#/services/planService";

export const planSlice = createSlice({
  name: "plan",
  initialState: {
    plan: {
      id: "",
      goal: "",
      subtasks: [],
      state: TaskState.OPEN_STATE,
    } as Task,
  },
  reducers: {
    setPlan: (state, action) => {
      state.plan = action.payload as Task;
    },
  },
});

export const { setPlan } = planSlice.actions;

export default planSlice.reducer;
