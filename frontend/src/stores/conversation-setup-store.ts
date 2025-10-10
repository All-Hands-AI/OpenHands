import { create } from "zustand";
import { AppConversationStartTask } from "#/api/open-hands.types";

interface ConversationSetupStore {
  isSetupMode: boolean;
  currentTask: AppConversationStartTask | null;
  conversationId: string | null;
  setIsSetupMode: (isSetupMode: boolean) => void;
  setCurrentTask: (task: AppConversationStartTask | null) => void;
  setConversationId: (id: string | null) => void;
  reset: () => void;
}

const initialState = {
  isSetupMode: false,
  currentTask: null,
  conversationId: null,
};

export const useConversationSetupStore = create<ConversationSetupStore>(
  (set) => ({
    ...initialState,
    setIsSetupMode: (isSetupMode) => set({ isSetupMode }),
    setCurrentTask: (task) => set({ currentTask: task }),
    setConversationId: (id) => set({ conversationId: id }),
    reset: () => set(initialState),
  }),
);
