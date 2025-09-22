import { createSlice } from "@reduxjs/toolkit";

export type ConversationTab =
  | "editor"
  | "browser"
  | "jupyter"
  | "served"
  | "vscode"
  | "terminal";

export interface IMessageToSend {
  text: string;
  timestamp: number;
}

interface ConversationState {
  isRightPanelShown: boolean;
  selectedTab: ConversationTab | null;
  images: File[];
  files: File[];
  loadingFiles: string[]; // File names currently being processed
  loadingImages: string[]; // Image names currently being processed
  messageToSend: IMessageToSend | null;
  shouldShownAgentLoading: boolean;
  submittedMessage: string | null;
  shouldHideSuggestions: boolean; // New state to hide suggestions when input expands
  hasRightPanelToggled: boolean;
}

export const conversationSlice = createSlice({
  name: "conversation",
  initialState: {
    isRightPanelShown: true,
    selectedTab: "editor" as ConversationTab,
    shouldStopConversation: false,
    shouldStartConversation: false,
    images: [],
    files: [],
    loadingFiles: [],
    loadingImages: [],
    messageToSend: null,
    shouldShownAgentLoading: false,
    submittedMessage: null,
    shouldHideSuggestions: false, // Initialize to false
    hasRightPanelToggled: true,
  } as ConversationState,
  reducers: {
    setIsRightPanelShown: (state, action) => {
      state.isRightPanelShown = action.payload;
    },
    setSelectedTab: (state, action) => {
      state.selectedTab = action.payload;
    },
    setShouldShownAgentLoading: (state, action) => {
      state.shouldShownAgentLoading = action.payload;
    },
    setShouldHideSuggestions: (state, action) => {
      state.shouldHideSuggestions = action.payload;
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
      state.messageToSend = {
        text: action.payload,
        timestamp: Date.now(),
      };
    },
    setSubmittedMessage: (state, action) => {
      state.submittedMessage = action.payload;
    },
    // Reset conversation state (useful for cleanup)
    resetConversationState: (state) => {
      state.shouldHideSuggestions = false;
    },
    setHasRightPanelToggled: (state, action) => {
      state.hasRightPanelToggled = action.payload;
    },
  },
});

export const {
  setIsRightPanelShown,
  setSelectedTab,
  setShouldShownAgentLoading,
  setShouldHideSuggestions,
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
  setSubmittedMessage,
  resetConversationState,
  setHasRightPanelToggled,
} = conversationSlice.actions;

export default conversationSlice.reducer;
