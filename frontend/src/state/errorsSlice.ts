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
    removeError: (state, action) => {
      state.errors = state.errors.filter((error) => error !== action.payload);
    },
  },
});

export const { appendError, removeError } = errorsSlice.actions;

export default errorsSlice.reducer;
