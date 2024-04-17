import { configureStore } from "@reduxjs/toolkit";
import browserReducer from "./state/browserSlice";
import chatReducer from "./state/chatSlice";
import codeReducer from "./state/codeSlice";
import commandReducer from "./state/commandSlice";
import errorsReducer from "./state/errorsSlice";
import planReducer from "./state/planSlice";
import settingsReducer from "./state/settingsSlice";
import taskReducer from "./state/taskSlice";

const store = configureStore({
  reducer: {
    browser: browserReducer,
    chat: chatReducer,
    code: codeReducer,
    cmd: commandReducer,
    task: taskReducer,
    errors: errorsReducer,
    settings: settingsReducer,
    plan: planReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export default store;
