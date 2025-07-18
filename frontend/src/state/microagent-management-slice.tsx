import { createSlice } from "@reduxjs/toolkit";

export const microagentManagementSlice = createSlice({
  name: "microagentManagement",
  initialState: {
    selectedMicroagent: null,
    addMicroagentModalVisible: false,
    selectedRepository: null,
  },
  reducers: {
    setSelectedMicroagent: (state, action) => {
      state.selectedMicroagent = action.payload;
    },
    setAddMicroagentModalVisible: (state, action) => {
      state.addMicroagentModalVisible = action.payload;
    },
    setSelectedRepository: (state, action) => {
      state.selectedRepository = action.payload;
    },
  },
});

export const {
  setSelectedMicroagent,
  setAddMicroagentModalVisible,
  setSelectedRepository,
} = microagentManagementSlice.actions;

export default microagentManagementSlice.reducer;
