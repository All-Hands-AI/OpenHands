import { create } from "zustand";
import { OpenHandsEvent } from "#/types/v1/core";
import { handleEventForUI } from "#/utils/handle-event-for-ui";

interface EventState {
  events: OpenHandsEvent[];
  uiEvents: OpenHandsEvent[];
  addEvent: (event: OpenHandsEvent) => void;
}

export const useEventStore = create<EventState>()((set) => ({
  events: [],
  uiEvents: [],
  addEvent: (event: OpenHandsEvent) =>
    set((state) => {
      const newEvents = [...state.events, event];
      const newUiEvents = handleEventForUI(event, state.uiEvents);

      return {
        events: newEvents,
        uiEvents: newUiEvents,
      };
    }),
}));
