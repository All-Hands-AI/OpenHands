import { createSlice } from "@reduxjs/toolkit";

interface SpeechState {
  enabled: boolean;
}

const initialState: SpeechState = {
  enabled: false,
};

export const speechSlice = createSlice({
  name: "speech",
  initialState,
  reducers: {
    toggleSpeech: (state) => {
      const newState = !state.enabled;
      state.enabled = newState;
      // Cancel any ongoing speech when disabled
      if (!newState && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    },
  },
});

export const { toggleSpeech } = speechSlice.actions;
export default speechSlice.reducer;
