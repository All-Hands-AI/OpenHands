import { combineReducers, configureStore } from "@reduxjs/toolkit";
import agentReducer from "./state/agent-slice";
import browserReducer from "./state/browser-slice";
import microagentManagementReducer from "./state/microagent-management-slice";
import eventMessageReducer from "./state/event-message-slice";

export const rootReducer = combineReducers({
  browser: browserReducer,
  agent: agentReducer,
  microagentManagement: microagentManagementReducer,
  eventMessage: eventMessageReducer,
});

const store = configureStore({
  reducer: rootReducer,
});

export type RootState = ReturnType<typeof store.getState>;
export type AppStore = typeof store;
export type AppDispatch = typeof store.dispatch;

export default store;
