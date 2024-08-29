import { combineReducers, configureStore } from "@reduxjs/toolkit";
import chatReducer from "./state/chatSlice";
import codeReducer from "./state/codeSlice";
import securityAnalyzerReducer from "./state/securityAnalyzerSlice";

export const rootReducer = combineReducers({
  chat: chatReducer,
  code: codeReducer,
  securityAnalyzer: securityAnalyzerReducer,
});

const store = configureStore({
  reducer: rootReducer,
});

export type RootState = ReturnType<typeof store.getState>;
export type AppStore = typeof store;
export type AppDispatch = typeof store.dispatch;

export default store;
