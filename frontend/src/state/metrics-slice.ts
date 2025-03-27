import { createSlice, PayloadAction } from "@reduxjs/toolkit";

// Define model context window sizes (in tokens)
export const MODEL_CONTEXT_SIZES: Record<string, number> = {
  // Claude models
  "claude-3-7-sonnet-20250219": 200000,
  "claude-3-5-sonnet-20241022": 200000,
  "claude-3-5-sonnet-20240620": 200000,
  "claude-3-5-haiku-20241022": 200000,
  "claude-3-haiku-20240307": 200000,
  "claude-3-opus-20240229": 200000,
  "claude-3-sonnet-20240229": 200000,
  // GPT models
  "gpt-4o": 128000,
  "gpt-4-turbo": 128000,
  "gpt-4": 8192,
  "gpt-3.5-turbo": 16385,
  // Default fallback
  default: 100000,
};

interface TokenUsage {
  prompt_tokens: number;
  completion_tokens: number;
  cache_read_tokens: number;
  cache_write_tokens: number;
  model?: string;
}

interface ModelInfo {
  max_tokens?: number;
  max_input_tokens?: number;
  max_output_tokens?: number;
  [key: string]: unknown;
}

interface MetricsState {
  cost: number | null;
  usage: TokenUsage | null;
  mostRecentUsage: TokenUsage | null;
  modelName: string | null;
  modelInfo: ModelInfo | null;
}

const initialState: MetricsState = {
  cost: null,
  usage: null,
  mostRecentUsage: null,
  modelName: null,
  modelInfo: null,
};

const metricsSlice = createSlice({
  name: "metrics",
  initialState,
  reducers: {
    setMetrics: (
      state,
      action: PayloadAction<{
        cost: number | null;
        usage: TokenUsage | null;
        token_usages?: TokenUsage[];
        model_name?: string;
        model_info?: ModelInfo;
      }>,
    ) => {
      state.cost = action.payload.cost;
      state.usage = action.payload.usage;

      // Set the model name if provided
      if (action.payload.model_name) {
        state.modelName = action.payload.model_name;
      }

      // Set the model info if provided
      if (action.payload.model_info) {
        state.modelInfo = action.payload.model_info;
      }

      // Set the most recent usage if token_usages is provided and has entries
      if (
        action.payload.token_usages &&
        action.payload.token_usages.length > 0
      ) {
        state.mostRecentUsage =
          action.payload.token_usages[action.payload.token_usages.length - 1];
      }
    },
  },
});

export const { setMetrics } = metricsSlice.actions;
export default metricsSlice.reducer;
