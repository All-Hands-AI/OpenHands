import { createSlice } from "@reduxjs/toolkit";
import { Plan, TaskState } from "#/services/planService";

export const planSlice = createSlice({
  name: "plan",
  initialState: {
    plan: {
      mainGoal: undefined,
      task: {
        id: "",
        goal: "",
        parent: "Task | None",
        subtasks: [],
        state: TaskState.OPEN_STATE,
      },
    } as Plan,
  },
  reducers: {
    setPlan: (state, action) => {
      state.plan = action.payload as Plan;
    },
  },
});

export const { setPlan } = planSlice.actions;

export default planSlice.reducer;
