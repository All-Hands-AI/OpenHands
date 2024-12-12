import { createSlice } from "@reduxjs/toolkit";

interface SpeechState {
  enabled: boolean;
}

const initialState: SpeechState = {
  enabled: true,
};

export const speechSlice = createSlice({
  name: "speech",
  initialState,
  reducers: {
    toggleSpeech: (state) => {
      state.enabled = !state.enabled;
      // Cancel any ongoing speech when disabled
      if (!state.enabled) {
        window.speechSynthesis.cancel();
      }
    },
  },
});

export const { toggleSpeech } = speechSlice.actions;
export default speechSlice.reducer;
