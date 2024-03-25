import { configureStore } from "@reduxjs/toolkit";
import browserReducer from "./state/browserSlice";
import chatReducer from "./state/chatSlice";
import codeReducer from "./state/codeSlice";
import taskReducer from "./state/taskSlice";
import errorsReducer from "./state/errorsSlice";

const store = configureStore({
  reducer: {
    browser: browserReducer,
    chat: chatReducer,
    code: codeReducer,
    task: taskReducer,
    errors: errorsReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export default store;
