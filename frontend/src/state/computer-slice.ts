import { createSlice } from "@reduxjs/toolkit";

export const initialState = {
  computerList: [],
  eventID: null,
  tasksProgress: [],
};

export const computerSlice = createSlice({
  name: "computer",
  initialState,
  reducers: {
    setComputerList: (state, action) => {
      state.computerList.push(action.payload);
    },
    setTasksProgress: (state, action) => {
      state.tasksProgress.push(action.payload);
    },
    setEventID: (state, action) => {
      state.eventID = action.payload;
    },
    clearComputerList: (state) => {
      state.computerList = [];
    },
  },
});

export const {
  setComputerList,
  setEventID,
  clearComputerList,
  setTasksProgress,
} = computerSlice.actions;

export default computerSlice.reducer;
