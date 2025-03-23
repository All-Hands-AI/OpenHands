// This file is a placeholder for backward compatibility with tests
// All Redux functionality has been migrated to React Query and Context API

// Define empty types for backward compatibility with tests
export type RootState = Record<string, never>;
export type AppStore = {
  getState: () => RootState;
  dispatch: (action: unknown) => void;
};
export type AppDispatch = (action: unknown) => void;

// Create a dummy store for backward compatibility
const store = {
  getState: () => ({}),
  dispatch: () => {},
};

export default store;
