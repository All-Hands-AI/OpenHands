import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface MetricsState {
  cost: number | null;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  } | null;
}

const initialState: MetricsState = {
  cost: null,
  usage: null,
};

const metricsSlice = createSlice({
  name: "metrics",
  initialState,
  reducers: {
    setMetrics: (state, action: PayloadAction<MetricsState>) => {
      state.cost = action.payload.cost;
      state.usage = action.payload.usage;
    },
  },
});

export const { setMetrics } = metricsSlice.actions;
export default metricsSlice.reducer;
