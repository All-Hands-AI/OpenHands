import { combineReducers, configureStore } from "@reduxjs/toolkit";
// All slices are now handled by React Query

export const rootReducer = combineReducers({
  // All slices have been migrated to React Query
});

const store = configureStore({
  reducer: rootReducer,
});

export type RootState = ReturnType<typeof store.getState>;
export type AppStore = typeof store;
export type AppDispatch = typeof store.dispatch;

export default store;
