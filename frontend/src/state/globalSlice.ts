import { createSlice } from "@reduxjs/toolkit";

export const globalSlice = createSlice({
  name: "global",
  initialState: {
    initialized: false,
  },
  reducers: {
    setInitialized: (state, action) => {
      state.initialized = action.payload;
    },
  },
});

export const { setInitialized } = globalSlice.actions;

export default globalSlice.reducer;
