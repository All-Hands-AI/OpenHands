import { combineReducers, configureStore } from "@reduxjs/toolkit";
import { jupyterReducer } from "./state/jupyter-slice";
import microagentManagementReducer from "./state/microagent-management-slice";

export const rootReducer = combineReducers({
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
