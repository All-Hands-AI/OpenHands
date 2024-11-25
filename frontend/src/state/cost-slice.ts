import { createSlice, PayloadAction } from "@reduxjs/toolkit";

type CostState = {
  totalCost: number;
  lastStepCosts: { cost: number; description: string }[];
};

const initialState: CostState = {
  totalCost: 0,
  lastStepCosts: [],
};

export const costSlice = createSlice({
  name: "cost",
  initialState,
  reducers: {
    addStepCost(
      state,
      action: PayloadAction<{ stepCost: number; totalCost: number; description: string }>,
    ) {
      state.totalCost = action.payload.totalCost;
      state.lastStepCosts.push({
        cost: action.payload.stepCost,
        description: action.payload.description,
      });
      // Keep only last 3 step costs
      if (state.lastStepCosts.length > 3) {
        state.lastStepCosts.shift();
      }
    },
    clearCosts(state) {
      state.totalCost = 0;
      state.lastStepCosts = [];
    },
  },
});

export const { addStepCost, clearCosts } = costSlice.actions;
export default costSlice.reducer;
