import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface ConversationState {
  isRightPanelShown: boolean;
  isChatInputExpanded: boolean;
  images: File[];
  files: File[];
  messageToSend: string | null;
  dataFromExpandedChatInput: {
    message: string;
    images: File[];
    files: File[];
  } | null;
  shouldStopAgent: boolean;
}

const initialState: ConversationState = {
  isRightPanelShown: true,
  isChatInputExpanded: false,
  images: [],
  files: [],
  messageToSend: null,
  dataFromExpandedChatInput: null,
  shouldStopAgent: false,
};

export const conversationSlice = createSlice({
  name: "conversation",
  initialState,
  reducers: {
    setIsRightPanelShown: (state, action: PayloadAction<boolean>) => {
      state.isRightPanelShown = action.payload;
    },
    setIsChatInputExpanded: (state, action: PayloadAction<boolean>) => {
      state.isChatInputExpanded = action.payload;
    },
    setImages: (state, action: PayloadAction<File[]>) => {
      state.images = action.payload;
    },
    setFiles: (state, action: PayloadAction<File[]>) => {
      state.files = action.payload;
    },
    addImages: (state, action: PayloadAction<File[]>) => {
      state.images = [...state.images, ...action.payload];
    },
    addFiles: (state, action: PayloadAction<File[]>) => {
      state.files = [...state.files, ...action.payload];
    },
    removeImage: (state, action: PayloadAction<number>) => {
      state.images.splice(action.payload, 1);
    },
    removeFile: (state, action: PayloadAction<number>) => {
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
    },
    setMessageToSend: (state, action: PayloadAction<string | null>) => {
      state.messageToSend = action.payload;
    },
    setDataFromExpandedChatInput: (
      state,
      action: PayloadAction<{
        message: string;
        images: File[];
        files: File[];
      } | null>,
    ) => {
      state.dataFromExpandedChatInput = action.payload;
    },
    setShouldStopAgent: (state, action: PayloadAction<boolean>) => {
      state.shouldStopAgent = action.payload;
    },
  },
});

export const {
  setIsRightPanelShown,
  setIsChatInputExpanded,
  setImages,
  setFiles,
  addImages,
  addFiles,
  removeImage,
  removeFile,
  clearImages,
  clearFiles,
  clearAllFiles,
  setMessageToSend,
  setDataFromExpandedChatInput,
  setShouldStopAgent,
} = conversationSlice.actions;

export default conversationSlice.reducer;
