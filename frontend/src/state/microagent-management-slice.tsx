import { createSlice } from "@reduxjs/toolkit";
import { GitRepository } from "#/types/git";
import { EventMicroagentStatus } from "#/types/microagent-status";

export const microagentManagementSlice = createSlice({
  name: "microagentManagement",
  initialState: {
    selectedMicroagent: null,
    addMicroagentModalVisible: false,
    selectedRepository: null as GitRepository | null,
    personalRepositories: [] as GitRepository[],
    organizationRepositories: [] as GitRepository[],
    repositories: [] as GitRepository[],
    microagentStatuses: [] as EventMicroagentStatus[],
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
    setMicroagentStatuses: (state, action) => {
      state.microagentStatuses = action.payload;
    },
    addMicroagentStatus: (state, action) => {
      state.microagentStatuses.push(action.payload);
    },
    updateMicroagentStatus: (state, action) => {
      const { conversationId, status, prUrl } = action.payload;
      const statusEntry = state.microagentStatuses.find(
        (entry) => entry.conversationId === conversationId,
      );
      if (statusEntry) {
        statusEntry.status = status;
        if (prUrl) {
          statusEntry.prUrl = prUrl;
        }
      }
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
  setMicroagentStatuses,
  addMicroagentStatus,
  updateMicroagentStatus,
} = microagentManagementSlice.actions;

export default microagentManagementSlice.reducer;
