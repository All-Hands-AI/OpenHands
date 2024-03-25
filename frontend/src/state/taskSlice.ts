import { createSlice } from "@reduxjs/toolkit";

export const taskSlice = createSlice({
  name: "task",
  initialState: {
    initialized: false,
    completed: false,
  },
  reducers: {
    setInitialized: (state, action) => {
      state.initialized = action.payload;
    },
    setCompleted: (state, action) => {
      state.completed = action.payload;
    },
  },
});

export const { setInitialized, setCompleted } = taskSlice.actions;

export default taskSlice.reducer;
