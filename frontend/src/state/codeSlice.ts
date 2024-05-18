import { createSlice } from "@reduxjs/toolkit";

export const initialState = {
  code: "",
  path: "",
  refreshID: 0,
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
    setRefreshID: (state, action) => {
      state.refreshID = action.payload;
    },
  },
});

export const { setCode, setActiveFilepath, setRefreshID } = codeSlice.actions;

export default codeSlice.reducer;
