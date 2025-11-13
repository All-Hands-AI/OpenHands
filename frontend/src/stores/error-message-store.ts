import { create } from "zustand";

interface ErrorMessageState {
  errorMessage: string | null;
}

interface ErrorMessageActions {
  setErrorMessage: (message: string) => void;
  removeErrorMessage: () => void;
}

type ErrorMessageStore = ErrorMessageState & ErrorMessageActions;

const initialState: ErrorMessageState = {
  errorMessage: null,
};

export const useErrorMessageStore = create<ErrorMessageStore>((set) => ({
  ...initialState,

  setErrorMessage: (message: string) =>
    set(() => ({
      errorMessage: message,
    })),

  removeErrorMessage: () =>
    set(() => ({
      errorMessage: null,
    })),
}));
