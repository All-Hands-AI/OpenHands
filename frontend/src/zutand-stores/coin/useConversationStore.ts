import { create } from "zustand"

export enum CoinType {
  AGENT = "agent",
  MEME = "meme",
  DEFAI = "defai",
}

export type ConversationState = {
  initMsg: string
  agent: string
}

export type CoinStateAction = {
  handleSetInitMsg: (stakeInfo: ConversationState["initMsg"]) => void
  handleSetAgent: (stakeInfo: ConversationState["agent"]) => void
  resetState: () => void
}

const initialState: ConversationState = { initMsg: null, agent: null }

export type DepositStoreType = ConversationState & { actions: CoinStateAction }

const useConversationStore = create<DepositStoreType>()((set) => ({
  //States
  ...initialState,

  //Actions
  actions: {
    handleSetInitMsg: (initMsg) => set({ initMsg }),
    handleSetAgent: (agent) => set({ agent }),

    resetState: () =>
      set((state) => {
        state.initMsg = null

        return state
      }),
  },
}))

export default useConversationStore
