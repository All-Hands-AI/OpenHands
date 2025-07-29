import { createSlice } from "@reduxjs/toolkit";
import { GitRepository } from "#/types/git";
import { IMicroagentItem } from "#/types/microagent-management";

export const microagentManagementSlice = createSlice({
  name: "microagentManagement",
  initialState: {
    addMicroagentModalVisible: false,
    updateMicroagentModalVisible: false,
    selectedRepository: null as GitRepository | null,
    personalRepositories: [] as GitRepository[],
    organizationRepositories: [] as GitRepository[],
    repositories: [] as GitRepository[],
    selectedMicroagentItem: null as IMicroagentItem | null,
    learnThisRepoModalVisible: false,
  },
  reducers: {
    setAddMicroagentModalVisible: (state, action) => {
      state.addMicroagentModalVisible = action.payload;
    },
    setUpdateMicroagentModalVisible: (state, action) => {
      state.updateMicroagentModalVisible = action.payload;
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
    setSelectedMicroagentItem: (state, action) => {
      state.selectedMicroagentItem = action.payload;
    },
    setLearnThisRepoModalVisible: (state, action) => {
      state.learnThisRepoModalVisible = action.payload;
    },
  },
});

export const {
  setAddMicroagentModalVisible,
  setUpdateMicroagentModalVisible,
  setSelectedRepository,
  setPersonalRepositories,
  setOrganizationRepositories,
  setRepositories,
  setSelectedMicroagentItem,
  setLearnThisRepoModalVisible,
} = microagentManagementSlice.actions;

export default microagentManagementSlice.reducer;
