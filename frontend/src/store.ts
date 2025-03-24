import { configureStore } from "@reduxjs/toolkit";
// All slices (chat, browser, code, fileState, command, jupyter, securityAnalyzer, status, metrics, initialQuery, and agent) are now handled by React Query

// Dummy reducer to satisfy Redux requirements
const dummyReducer = (state = {}) => state;

export const rootReducer = {
  dummy: dummyReducer,
};

const store = configureStore({
  reducer: rootReducer,
});

export type RootState = ReturnType<typeof store.getState>;
export type AppStore = typeof store;
export type AppDispatch = typeof store.dispatch;

export default store;
