import { createSlice } from "@reduxjs/toolkit";

export const taskSlice = createSlice({
  name: "task",
  initialState: {
    completed: false,
  },
  reducers: {
    setCompleted: (state, action) => {
      state.completed = action.payload;
    },
  },
});

export const { setCompleted } = taskSlice.actions;

export default taskSlice.reducer;
