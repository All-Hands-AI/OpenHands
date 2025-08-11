import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface TerminalInputState {
  textToInsert: string | null;
}

const initialState: TerminalInputState = {
  textToInsert: null,
};

export const terminalInputSlice = createSlice({
  name: 'terminalInput',
  initialState,
  reducers: {
    insertText: (state, action: PayloadAction<string>) => {
      state.textToInsert = action.payload;
    },
    clearText: (state) => {
      state.textToInsert = null;
    },
  },
});

export const { insertText, clearText } = terminalInputSlice.actions;

export default terminalInputSlice.reducer;
