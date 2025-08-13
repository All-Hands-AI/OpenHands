import { createSlice } from "@reduxjs/toolkit";

interface ConversationState {
  isRightPanelShown: boolean;
  images: File[];
  files: File[];
  loadingFiles: string[]; // File names currently being processed
  loadingImages: string[]; // Image names currently being processed
  messageToSend: string | null;
}

export const conversationSlice = createSlice({
  name: "conversation",
  initialState: {
    isRightPanelShown: true,
    images: [],
    files: [],
    loadingFiles: [],
    loadingImages: [],
    messageToSend: null,
  } as ConversationState,
  reducers: {
    setIsRightPanelShown: (state, action) => {
      state.isRightPanelShown = action.payload;
    },
    addImages: (state, action) => {
      state.images = [...state.images, ...action.payload];
    },
    addFiles: (state, action) => {
      state.files = [...state.files, ...action.payload];
    },
    removeImage: (state, action) => {
      state.images.splice(action.payload, 1);
    },
    removeFile: (state, action) => {
      state.files.splice(action.payload, 1);
    },
    clearImages: (state) => {
      state.images = [];
    },
    clearFiles: (state) => {
      state.files = [];
    },
    clearAllFiles: (state) => {
      state.images = [];
      state.files = [];
      state.loadingFiles = [];
      state.loadingImages = [];
    },
    // Loading state management
    addFileLoading: (state, action) => {
      if (!state.loadingFiles.includes(action.payload)) {
        state.loadingFiles.push(action.payload);
      }
    },
    removeFileLoading: (state, action) => {
      state.loadingFiles = state.loadingFiles.filter(
        (name) => name !== action.payload,
      );
    },
    addImageLoading: (state, action) => {
      if (!state.loadingImages.includes(action.payload)) {
        state.loadingImages.push(action.payload);
      }
    },
    removeImageLoading: (state, action) => {
      state.loadingImages = state.loadingImages.filter(
        (name) => name !== action.payload,
      );
    },
    clearAllLoading: (state) => {
      state.loadingFiles = [];
      state.loadingImages = [];
    },
    setMessageToSend: (state, action) => {
      state.messageToSend = action.payload;
    },
  },
});

export const {
  setIsRightPanelShown,
  addImages,
  addFiles,
  removeImage,
  removeFile,
  clearImages,
  clearFiles,
  clearAllFiles,
  addFileLoading,
  removeFileLoading,
  addImageLoading,
  removeImageLoading,
  clearAllLoading,
  setMessageToSend,
} = conversationSlice.actions;

export default conversationSlice.reducer;
