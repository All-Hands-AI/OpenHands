import { combineReducers, configureStore } from "@reduxjs/toolkit";
import agentReducer from "./state/agent-slice";
import browserReducer from "./state/browser-slice";
import fileStateReducer from "./state/file-state-slice";
import { jupyterReducer } from "./state/jupyter-slice";
import securityAnalyzerReducer from "./state/security-analyzer-slice";
import microagentManagementReducer from "./state/microagent-management-slice";
import conversationReducer from "./state/conversation-slice";
import eventMessageReducer from "./state/event-message-slice";

export const rootReducer = combineReducers({
  fileState: fileStateReducer,
  browser: browserReducer,
  agent: agentReducer,
  jupyter: jupyterReducer,
  securityAnalyzer: securityAnalyzerReducer,
  microagentManagement: microagentManagementReducer,
  conversation: conversationReducer,
  eventMessage: eventMessageReducer,
});

const store = configureStore({
  reducer: rootReducer,
});

export type RootState = ReturnType<typeof store.getState>;
export type AppStore = typeof store;
export type AppDispatch = typeof store.dispatch;

export default store;
