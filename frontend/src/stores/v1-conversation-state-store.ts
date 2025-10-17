import { create } from "zustand";
import { V1AgentStatus } from "#/types/v1/core/base/common";

interface V1ConversationStateStore {
  agent_status: V1AgentStatus | null;

  /**
   * Set the agent status
   */
  setAgentStatus: (agent_status: V1AgentStatus) => void;

  /**
   * Reset the store to initial state
   */
  reset: () => void;
}

export const useV1ConversationStateStore = create<V1ConversationStateStore>(
  (set) => ({
    agent_status: null,

    setAgentStatus: (agent_status: V1AgentStatus) => set({ agent_status }),

    reset: () => set({ agent_status: null }),
  }),
);
