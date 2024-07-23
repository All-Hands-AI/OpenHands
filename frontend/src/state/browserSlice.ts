import { createSlice } from "@reduxjs/toolkit";
import { updateBrowserTabUrl } from "#/services/browseService";

export const initialState = {
  // URL of browser window (placeholder for now, will be replaced with the actual URL later)
  url: "https://github.com/OpenDevin/OpenDevin",
  // Base64-encoded screenshot of browser window (placeholder for now, will be replaced with the actual screenshot later)
  screenshotSrc: "",
};

export const browserSlice = createSlice({
  name: "browser",
  initialState,
  reducers: {
    setUrl: (state, action) => {
      state.url = action.payload;
      updateBrowserTabUrl(action.payload);
    },
    setScreenshotSrc: (state, action) => {
      state.screenshotSrc = action.payload;
    },
    sendUrl: (state, action) => {
      state.url = action.payload;
      updateBrowserTabUrl(action.payload);
    },
  },
});

export const { setUrl, setScreenshotSrc, sendUrl } = browserSlice.actions;

export default browserSlice.reducer;
