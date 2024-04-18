import { combineReducers, configureStore } from "@reduxjs/toolkit";
import browserReducer from "./state/browserSlice";
import chatReducer from "./state/chatSlice";
import codeReducer from "./state/codeSlice";
import commandReducer from "./state/commandSlice";
import taskReducer from "./state/taskSlice";
import errorsReducer from "./state/errorsSlice";
import settingsReducer from "./state/settingsSlice";

export const rootReducer = combineReducers({
  browser: browserReducer,
  chat: chatReducer,
  code: codeReducer,
  cmd: commandReducer,
  task: taskReducer,
  errors: errorsReducer,
  settings: settingsReducer,
});

const store = configureStore({
  reducer: rootReducer,
});

export type RootState = ReturnType<typeof store.getState>;
export type AppStore = typeof store;
export type AppDispatch = typeof store.dispatch;

export default store;
