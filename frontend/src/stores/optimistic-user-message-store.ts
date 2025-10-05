import { create } from "zustand";

interface OptimisticUserMessageState {
  optimisticUserMessage: string | null;
}

interface OptimisticUserMessageActions {
  setOptimisticUserMessage: (message: string) => void;
  getOptimisticUserMessage: () => string | null;
  removeOptimisticUserMessage: () => void;
}

type OptimisticUserMessageStore = OptimisticUserMessageState &
  OptimisticUserMessageActions;

const initialState: OptimisticUserMessageState = {
  optimisticUserMessage: null,
};

export const useOptimisticUserMessageStore = create<OptimisticUserMessageStore>(
  (set, get) => ({
    ...initialState,

    setOptimisticUserMessage: (message: string) =>
      set(() => ({
        optimisticUserMessage: message,
      })),

    getOptimisticUserMessage: () => get().optimisticUserMessage,

    removeOptimisticUserMessage: () =>
      set(() => ({
        optimisticUserMessage: null,
      })),
  }),
);
