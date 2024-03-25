import { createSlice } from "@reduxjs/toolkit";

export const codeSlice = createSlice({
  name: "code",
  initialState: {
    code: "# Welcome to OpenDevin!",
  },
  reducers: {
    setCode: (state, action) => {
      state.code = action.payload;
    },
  },
});

export const { setCode } = codeSlice.actions;

export default codeSlice.reducer;
