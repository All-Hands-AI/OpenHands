import { combineReducers, configureStore } from "@reduxjs/toolkit";
import agentReducer from "./state/agent-slice";
import browserReducer from "./state/browser-slice";
import chatReducer from "./state/chat-slice";
import codeReducer from "./state/code-slice";
import fileStateReducer from "./state/file-state-slice";
import initialQueryReducer from "./state/initial-query-slice";
import commandReducer from "./state/command-slice";
import { jupyterReducer } from "./state/jupyter-slice";
import securityAnalyzerReducer from "./state/security-analyzer-slice";
// Status and metrics slices are now handled by React Query

export const rootReducer = combineReducers({
  fileState: fileStateReducer,
  initialQuery: initialQueryReducer,
  browser: browserReducer,
  chat: chatReducer,
  code: codeReducer,
  cmd: commandReducer,
  agent: agentReducer,
  jupyter: jupyterReducer,
  securityAnalyzer: securityAnalyzerReducer,
  // status and metrics slices removed (migrated to React Query)
});

const store = configureStore({
  reducer: rootReducer,
});

export type RootState = ReturnType<typeof store.getState>;
export type AppStore = typeof store;
export type AppDispatch = typeof store.dispatch;

export default store;
