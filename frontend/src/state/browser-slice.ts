import { createSlice } from "@reduxjs/toolkit";

export const initialState = {
  // URL of browser window (placeholder for now, will be replaced with the actual URL later)
  url: "https://github.com/All-Hands-AI/OpenHands",
  // Base64-encoded screenshot of browser window (placeholder for now, will be replaced with the actual screenshot later)
  screenshotSrc: "",
};

export const browserSlice = createSlice({
  name: "browser",
  initialState,
  reducers: {
    setUrl: (state, action) => {
      state.url = action.payload;
    },
    setScreenshotSrc: (state, action) => {
      state.screenshotSrc = action.payload;
    },
  },
});

export const { setUrl, setScreenshotSrc } = browserSlice.actions;

export default browserSlice.reducer;
