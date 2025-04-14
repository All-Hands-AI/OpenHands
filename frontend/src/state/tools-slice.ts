import { createSlice, PayloadAction } from "@reduxjs/toolkit";

export interface ToolParameter {
  type: string;
  description?: string;
  required?: boolean;
  enum?: string[];
  items?: {
    type: string;
  };
  properties?: Record<string, ToolParameter>;
}

export interface Tool {
  name: string;
  description?: string;
  parameters?: Record<string, ToolParameter>;
}

interface ToolsState {
  tools: Tool[] | null;
}

const initialState: ToolsState = {
  tools: null,
};

const toolsSlice = createSlice({
  name: "tools",
  initialState,
  reducers: {
    setTools: (state, action: PayloadAction<ToolsState>) => {
      console.log("Tools slice: setting tools", action.payload.tools);
      if (!action.payload.tools) {
        console.warn("Tools slice: received null or undefined tools");
      } else if (action.payload.tools.length === 0) {
        console.warn("Tools slice: received empty tools array");
      } else {
        console.log(
          "Tools slice: received",
          action.payload.tools.length,
          "tools",
        );
      }
      state.tools = action.payload.tools;
    },
  },
});

export const { setTools } = toolsSlice.actions;
export default toolsSlice.reducer;
