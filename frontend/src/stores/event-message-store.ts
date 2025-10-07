import { create } from "zustand";

interface EventMessageState {
  submittedEventIds: number[]; // Avoid the flashing issue of the confirmation buttons
}

interface EventMessageStore extends EventMessageState {
  addSubmittedEventId: (id: number) => void;
  removeSubmittedEventId: (id: number) => void;
}

export const useEventMessageStore = create<EventMessageStore>((set) => ({
  submittedEventIds: [],
  addSubmittedEventId: (id: number) =>
    set((state) => ({
      submittedEventIds: [...state.submittedEventIds, id],
    })),
  removeSubmittedEventId: (id: number) =>
    set((state) => ({
      submittedEventIds: state.submittedEventIds.filter(
        (eventId) => eventId !== id,
      ),
    })),
}));
