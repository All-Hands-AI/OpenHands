import { createSlice } from "@reduxjs/toolkit";

export const initialState = {
  code: "",
  path: "",
};

export const codeSlice = createSlice({
  name: "code",
  initialState,
  reducers: {
    setCode: (state, action) => {
      state.code = action.payload;
    },
    setActiveFilepath: (state, action) => {
      state.path = action.payload;
    },
  },
});

export const { setCode, setActiveFilepath } = codeSlice.actions;

export default codeSlice.reducer;
