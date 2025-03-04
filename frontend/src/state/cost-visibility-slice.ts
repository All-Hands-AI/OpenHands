import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface CostVisibilityState {
  isVisible: boolean;
}

const initialState: CostVisibilityState = {
  isVisible: true,
};

export const costVisibilitySlice = createSlice({
  name: "costVisibility",
  initialState,
  reducers: {
    setCostVisibility: (state, action: PayloadAction<boolean>) => {
      state.isVisible = action.payload;
    },
  },
});

export const { setCostVisibility } = costVisibilitySlice.actions;
export default costVisibilitySlice.reducer;
