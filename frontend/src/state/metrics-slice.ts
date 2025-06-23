import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface MetricsState {
  cost: number | null;
  max_budget_per_task: number | null;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    cache_read_tokens: number;
    cache_write_tokens: number;
    context_window: number;
    per_turn_token: number;
  } | null;
}

const initialState: MetricsState = {
  cost: null,
  max_budget_per_task: null,
  usage: null,
};

const metricsSlice = createSlice({
  name: "metrics",
  initialState,
  reducers: {
    setMetrics: (state, action: PayloadAction<MetricsState>) => {
      state.cost = action.payload.cost;
      state.max_budget_per_task = action.payload.max_budget_per_task;
      state.usage = action.payload.usage;
    },
  },
});

export const { setMetrics } = metricsSlice.actions;
export default metricsSlice.reducer;
