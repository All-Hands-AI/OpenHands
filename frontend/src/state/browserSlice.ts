import { createSlice } from "@reduxjs/toolkit";

export const browserSlice = createSlice({
  name: "browser",
  initialState: {
    // URL of browser window (placeholder for now, will be replaced with the actual URL later)
    url: "https://github.com/OpenDevin/OpenDevin",
    // Base64-encoded screenshot of browser window (placeholder for now, will be replaced with the actual screenshot later)
    screenshotSrc:
      "data:image/png;base64, iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mN0uGvyHwAFCAJS091fQwAAAABJRU5ErkJggg==",
  },
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
