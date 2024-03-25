import { createSlice } from "@reduxjs/toolkit";

const initialErrors: string[] = [];

export const errorsSlice = createSlice({
  name: "errors",
  initialState: {
    errors: initialErrors,
  },
  reducers: {
    appendError: (state, action) => {
      state.errors.push(action.payload);
    },
  },
});

export const { appendError } = errorsSlice.actions;

export default errorsSlice.reducer;
