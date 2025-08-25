import { createSlice } from "@reduxjs/toolkit";

export const eventMessageSlice = createSlice({
  name: "eventMessage",
  initialState: {
    submittedEventIds: [] as number[], // Avoid the flashing issue of the confirmation buttons
  },
  reducers: {
    addSubmittedEventId: (state, action) => {
      state.submittedEventIds.push(action.payload);
    },
    removeSubmittedEventId: (state, action) => {
      state.submittedEventIds = state.submittedEventIds.filter(
        (id) => id !== action.payload,
      );
    },
  },
});

export const { addSubmittedEventId, removeSubmittedEventId } =
  eventMessageSlice.actions;

export default eventMessageSlice.reducer;
