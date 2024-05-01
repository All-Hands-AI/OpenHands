import { combineReducers, configureStore } from "@reduxjs/toolkit";
import agentReducer from "./state/agentSlice";
import browserReducer from "./state/browserSlice";
import chatReducer from "./state/chatSlice";
import chat from "./state/chat";
import codeReducer from "./state/codeSlice";
import commandReducer from "./state/commandSlice";
import errorsReducer from "./state/errorsSlice";
import planReducer from "./state/planSlice";
import taskReducer from "./state/taskSlice";
import jupyterReducer from "./state/jupyterSlice";

export const rootReducer = combineReducers({
  browser: browserReducer,
  chat: chatReducer,
  tempChat: chat,
  code: codeReducer,
  cmd: commandReducer,
  task: taskReducer,
  errors: errorsReducer,
  plan: planReducer,
  agent: agentReducer,
  jupyter: jupyterReducer,
});

const store = configureStore({
  reducer: rootReducer,
});

export type RootState = ReturnType<typeof store.getState>;
export type AppStore = typeof store;
export type AppDispatch = typeof store.dispatch;

export default store;
