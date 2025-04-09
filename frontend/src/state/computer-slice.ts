import { createSlice } from "@reduxjs/toolkit";

export const initialState = {
  computerList: [],
};

export const computerSlice = createSlice({
  name: "computer",
  initialState,
  reducers: {
    setComputerList: (state, action) => {
      state.computerList.push(action.payload);
    },
  },
});

export const { setComputerList } = computerSlice.actions;

export default computerSlice.reducer;
