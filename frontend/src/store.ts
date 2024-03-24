import { configureStore } from "@reduxjs/toolkit";
import browserReducer from "./state/browserSlice";
import chatReducer from "./state/chatSlice";

const store = configureStore({
  reducer: {
    browser: browserReducer,
    chat: chatReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export default store;
