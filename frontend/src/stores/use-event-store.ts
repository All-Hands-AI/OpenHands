import { create } from "zustand";
import { OpenHandsEvent } from "#/types/v1/core";
import { handleEventForUI } from "#/utils/handle-event-for-ui";
import { OpenHandsParsedEvent } from "#/types/core";

interface EventState {
  events: OpenHandsParsedEvent[];
  uiEvents: OpenHandsParsedEvent[];
  addEvent: (event: OpenHandsParsedEvent) => void;
  clearEvents: () => void;
}

export const useEventStore = create<EventState>()((set) => ({
  events: [],
  uiEvents: [],
  addEvent: (event: OpenHandsParsedEvent) =>
    set((state) => {
      const newEvents = [...state.events, event];
      const newUiEvents = handleEventForUI(event, state.uiEvents);

      return {
        events: newEvents,
        uiEvents: newUiEvents,
      };
    }),
  clearEvents: () =>
    set(() => ({
      events: [],
      uiEvents: [],
    })),
}));
