import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface LLMMetrics {
  accumulatedCost: number;
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
}

const initialState: LLMMetrics = {
  accumulatedCost: 0,
  promptTokens: 0,
  completionTokens: 0,
  totalTokens: 0,
};

const llmMetricsSlice = createSlice({
  name: "llmMetrics",
  initialState,
  reducers: {
    updateLLMMetrics: (state, action: PayloadAction<Partial<LLMMetrics>>) => {
      return { ...state, ...action.payload };
    },
    resetLLMMetrics: () => initialState,
  },
});

export const { updateLLMMetrics, resetLLMMetrics } = llmMetricsSlice.actions;
export default llmMetricsSlice.reducer;
