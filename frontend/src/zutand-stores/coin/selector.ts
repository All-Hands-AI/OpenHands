import useConversationStore, { ConversationState } from "./useConversationStore"

export const useConversationActions = () =>
  useConversationStore((state) => state.actions)
export const useGetConversationState = <K extends keyof ConversationState>(
  key: K,
): ConversationState[K] => useConversationStore((state) => state[key])
