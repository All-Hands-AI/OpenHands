import { create } from "zustand";

interface ErrorMessageState {
  errorMessage: string | null;
}

interface ErrorMessageActions {
  setErrorMessage: (message: string) => void;
  getErrorMessage: () => string | null;
  removeErrorMessage: () => void;
}

type ErrorMessageStore = ErrorMessageState & ErrorMessageActions;

const initialState: ErrorMessageState = {
  errorMessage: null,
};

export const useErrorMessageStore = create<ErrorMessageStore>((set, get) => ({
  ...initialState,

  setErrorMessage: (message: string) =>
    set(() => ({
      errorMessage: message,
    })),

  getErrorMessage: () => get().errorMessage,

  removeErrorMessage: () =>
    set(() => ({
      errorMessage: null,
    })),
}));
