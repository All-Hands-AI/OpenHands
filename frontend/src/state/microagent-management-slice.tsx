import { createSlice } from "@reduxjs/toolkit";
import { GitRepository } from "#/types/git";
import { EventMicroagentStatus } from "#/types/microagent-status";
import { IMicroagentItem } from "#/types/microagent-management";

export const microagentManagementSlice = createSlice({
  name: "microagentManagement",
  initialState: {
    addMicroagentModalVisible: false,
    selectedRepository: null as GitRepository | null,
    personalRepositories: [] as GitRepository[],
    organizationRepositories: [] as GitRepository[],
    repositories: [] as GitRepository[],
    microagentStatuses: [] as EventMicroagentStatus[],
    selectedMicroagentItem: null as IMicroagentItem | null,
  },
  reducers: {
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
    setSelectedMicroagentItem: (state, action) => {
      state.selectedMicroagentItem = action.payload;
    },
  },
});

export const {
  setAddMicroagentModalVisible,
  setSelectedRepository,
  setPersonalRepositories,
  setOrganizationRepositories,
  setRepositories,
  setMicroagentStatuses,
  addMicroagentStatus,
  updateMicroagentStatus,
  setSelectedMicroagentItem,
} = microagentManagementSlice.actions;

export default microagentManagementSlice.reducer;
