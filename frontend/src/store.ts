// This file is kept for backward compatibility with any imports that might still exist
// All state management has been migrated to React Query

// Define empty types for backward compatibility
export type RootState = Record<string, never>;
export type AppStore = Record<string, never>;
export type AppDispatch = () => void;

// Export an empty object as the store
const store = {};
export default store;
