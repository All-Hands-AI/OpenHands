import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface ToolsState {
  tools: any[] | null;
}

const initialState: ToolsState = {
  tools: null,
};

const toolsSlice = createSlice({
  name: "tools",
  initialState,
  reducers: {
    setTools: (state, action: PayloadAction<ToolsState>) => {
      console.log("setTools action received:", action.payload);
      state.tools = action.payload.tools;
    },
  },
});

export const { setTools } = toolsSlice.actions;
export default toolsSlice.reducer;
