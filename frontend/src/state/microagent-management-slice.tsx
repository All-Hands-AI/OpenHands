import { createSlice } from "@reduxjs/toolkit";

export const microagentManagementSlice = createSlice({
  name: "microagentManagement",
  initialState: {
    selectedMicroagent: null,
  },
  reducers: {
    setSelectedMicroagent: (state, action) => {
      state.selectedMicroagent = action.payload;
    },
  },
});

export const { setSelectedMicroagent } = microagentManagementSlice.actions;

export default microagentManagementSlice.reducer;
