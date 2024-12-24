import { createAsyncThunk, createSlice, PayloadAction } from "@reduxjs/toolkit";
import OpenHands from "#/api/open-hands";
import { Settings } from "#/api/open-hands.types";

type SliceState = {
  settings: Settings | null;
  isLoading: boolean;
  error: string | null;
};

const initialState: SliceState = {
  settings: null,
  isLoading: false,
  error: null,
};

export const loadSettings = createAsyncThunk(
  "settings/loadSettings",
  async () => {
    const settings = await OpenHands.loadSettings();
    return settings;
  },
);

export const storeSettings = createAsyncThunk(
  "settings/storeSettings",
  async (settings: Settings) => {
    await OpenHands.storeSettings(settings);
    return settings;
  },
);

export const settingsSlice = createSlice({
  name: "settings",
  initialState,
  reducers: {
    updateSettings(state, action: PayloadAction<Partial<Settings>>) {
      state.settings = {
        ...state.settings,
        ...action.payload,
      };
    },
    clearSettings(state) {
      state.settings = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(loadSettings.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(loadSettings.fulfilled, (state, action) => {
        state.isLoading = false;
        state.settings = action.payload;
      })
      .addCase(loadSettings.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || "Failed to load settings";
      })
      .addCase(storeSettings.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(storeSettings.fulfilled, (state, action) => {
        state.isLoading = false;
        state.settings = action.payload;
      })
      .addCase(storeSettings.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || "Failed to store settings";
      });
  },
});

export const { updateSettings, clearSettings } = settingsSlice.actions;
export default settingsSlice.reducer;
