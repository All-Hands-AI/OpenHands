import { combineReducers, configureStore } from "@reduxjs/toolkit";
import agentReducer from "./state/agent-slice";
import chatReducer from "./state/chat-slice";
// browser, code, fileState, command, jupyter, securityAnalyzer, status, metrics, and initialQuery slices are now handled by React Query

export const rootReducer = combineReducers({
  chat: chatReducer,
  agent: agentReducer,
  // browser, code, fileState, command, jupyter, securityAnalyzer, status, metrics, and initialQuery slices removed (migrated to React Query)
});

const store = configureStore({
  reducer: rootReducer,
});

export type RootState = ReturnType<typeof store.getState>;
export type AppStore = typeof store;
export type AppDispatch = typeof store.dispatch;

export default store;
