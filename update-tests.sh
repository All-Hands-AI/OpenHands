#!/bin/bash

# Update test files to remove Redux references
sed -i 's/import { addUserMessage } from "#\/state\/chat-slice";/import { useChat } from "#\/hooks\/query\/use-chat";/g' /workspace/OpenHands/frontend/__tests__/components/chat/chat-interface.test.tsx
sed -i 's/import \* as ChatSlice from "#\/state\/chat-slice";/\/\/ ChatSlice imports removed/g' /workspace/OpenHands/frontend/__tests__/components/chat/chat-interface.test.tsx
sed -i 's/import \* as ChatSlice from "#\/state\/chat-slice";/\/\/ ChatSlice imports removed/g' /workspace/OpenHands/frontend/__tests__/context/ws-client-provider.test.tsx
sed -i 's/import { Provider } from "react-redux";/import { QueryClientProvider } from "@tanstack\/react-query";/g' /workspace/OpenHands/frontend/__tests__/components/jupyter/jupyter.test.tsx
sed -i 's/import { configureStore } from "@reduxjs\/toolkit";/import { queryClient } from "#\/query-client-init";/g' /workspace/OpenHands/frontend/__tests__/components/jupyter/jupyter.test.tsx
sed -i 's/import { initQueryReduxBridge } from "#\/utils\/query-redux-bridge";/import { initializeQueryClient } from "#\/query-client-init";/g' /workspace/OpenHands/frontend/__tests__/routes/_oh.app.test.tsx
sed -i 's/import store from "#\/store";/\/\/ store import removed/g' /workspace/OpenHands/frontend/__tests__/services/actions.test.ts
sed -i 's/import \* as queryReduxBridge from "#\/utils\/query-redux-bridge";/\/\/ queryReduxBridge import removed/g' /workspace/OpenHands/frontend/__tests__/services/actions.test.ts

# Update test-utils.tsx
sed -i 's/import { Provider } from "react-redux";/import { QueryClientProvider } from "@tanstack\/react-query";/g' /workspace/OpenHands/frontend/test-utils.tsx
sed -i 's/import { configureStore } from "@reduxjs\/toolkit";/import { queryClient } from ".\/src\/query-client-init";/g' /workspace/OpenHands/frontend/test-utils.tsx
sed -i 's/import { AppStore, RootState, rootReducer } from ".\/src\/store";/\/\/ store imports removed/g' /workspace/OpenHands/frontend/test-utils.tsx