import { combineReducers, configureStore } from "@reduxjs/toolkit";
import agentReducer from "./state/agent-slice";
import browserReducer from "./state/browser-slice";
import { jupyterReducer } from "./state/jupyter-slice";
import microagentManagementReducer from "./state/microagent-management-slice";

export const rootReducer = combineReducers({
  browser: browserReducer,
  agent: agentReducer,
  jupyter: jupyterReducer,
  microagentManagement: microagentManagementReducer,
});

const store = configureStore({
  reducer: rootReducer,
});

export type RootState = ReturnType<typeof store.getState>;
export type AppStore = typeof store;
export type AppDispatch = typeof store.dispatch;

export default store;
