import { createSlice } from "@reduxjs/toolkit";
import { GitRepository } from "#/types/git";

export const microagentManagementSlice = createSlice({
  name: "microagentManagement",
  initialState: {
    selectedMicroagent: null,
    addMicroagentModalVisible: false,
    selectedRepository: null,
    personalRepositories: [] as GitRepository[],
    organizationRepositories: [] as GitRepository[],
    repositories: [] as GitRepository[],
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
    setPersonalRepositories: (state, action) => {
      state.personalRepositories = action.payload;
    },
    setOrganizationRepositories: (state, action) => {
      state.organizationRepositories = action.payload;
    },
    setRepositories: (state, action) => {
      state.repositories = action.payload;
    },
  },
});

export const {
  setSelectedMicroagent,
  setAddMicroagentModalVisible,
  setSelectedRepository,
  setPersonalRepositories,
  setOrganizationRepositories,
  setRepositories,
} = microagentManagementSlice.actions;

export default microagentManagementSlice.reducer;
