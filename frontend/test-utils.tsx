// See https://redux.js.org/usage/writing-tests#setting-up-a-reusable-test-render-function for more information

import React, { PropsWithChildren } from "react";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import { RenderOptions, render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { I18nextProvider, initReactI18next } from "react-i18next";
import i18n from "i18next";
import { vi } from "vitest";
import { AppStore, RootState, rootReducer } from "./src/store";
import { AuthProvider } from "#/context/auth-context";
import { ConversationProvider } from "#/context/conversation-context";
import { SettingsUpToDateProvider } from "#/context/settings-up-to-date-context";

// Mock useParams before importing components
vi.mock("react-router", async () => {
  const actual =
    await vi.importActual<typeof import("react-router")>("react-router");
  return {
    ...actual,
    useParams: () => ({ conversationId: "test-conversation-id" }),
  };
});

// Initialize i18n for tests
i18n.use(initReactI18next).init({
  lng: "en",
  fallbackLng: "en",
  ns: ["translation"],
  defaultNS: "translation",
  resources: {
    en: {
      translation: {
        ACCOUNT_SETTINGS$SETTINGS: "Account Settings",
        ACCOUNT_SETTINGS$LOGOUT: "Logout",
        BROWSER$EMPTY_MESSAGE: "No browser content to display",
        CHAT_INTERFACE$AGENT_INIT_MESSAGE: "Agent is initializing...",
        CHAT_INTERFACE$AGENT_RUNNING_MESSAGE: "Agent is running...",
        CHAT_INTERFACE$AGENT_AWAITING_USER_INPUT_MESSAGE: "Waiting for user input...",
        CHAT_INTERFACE$AGENT_PAUSED_MESSAGE: "Agent is paused",
        CHAT_INTERFACE$INITIALIZING_AGENT_LOADING_MESSAGE: "Loading...",
        CHAT_INTERFACE$AGENT_STOPPED_MESSAGE: "Agent has stopped",
        CHAT_INTERFACE$AGENT_FINISHED_MESSAGE: "Agent has finished",
        CHAT_INTERFACE$AGENT_REJECTED_MESSAGE: "Agent was rejected",
        CHAT_INTERFACE$AGENT_ERROR_MESSAGE: "An error occurred",
        CHAT_INTERFACE$AGENT_AWAITING_USER_CONFIRMATION_MESSAGE: "Waiting for user confirmation...",
        CHAT_INTERFACE$AGENT_ACTION_USER_CONFIRMED_MESSAGE: "User confirmed",
        CHAT_INTERFACE$AGENT_ACTION_USER_REJECTED_MESSAGE: "User rejected",
        CHAT_INTERFACE$AGENT_RATE_LIMITED_MESSAGE: "Rate limited, please wait...",
        CHAT$LETS_START_BUILDING: "Let's start building!",
        STATUS$STARTING_RUNTIME: "Starting Runtime...",
        STATUS$STARTING_CONTAINER: "Preparing container, this might take a few minutes...",
        STATUS$PREPARING_CONTAINER: "Preparing to start container...",
        STATUS$CONTAINER_STARTED: "Container started.",
        STATUS$WAITING_FOR_CLIENT: "Waiting for client to become ready...",
        STATUS$ERROR_LLM_AUTHENTICATION: "Error authenticating with the LLM provider. Please check your API key",
        STATUS$ERROR_RUNTIME_DISCONNECTED: "There was an error while connecting to the runtime. Please refresh the page.",
        AGENT_ERROR$BAD_ACTION: "Agent tried to execute a malformed action.",
        AGENT_ERROR$ACTION_TIMEOUT: "Action timed out.",
        WORKSPACE$TITLE: "OpenHands Workspace",
        WORKSPACE$TERMINAL_TAB_LABEL: "Terminal",
        WORKSPACE$PLANNER_TAB_LABEL: "Planner",
        WORKSPACE$JUPYTER_TAB_LABEL: "Jupyter IPython",
        WORKSPACE$CODE_EDITOR_TAB_LABEL: "Code Editor",
        WORKSPACE$BROWSER_TAB_LABEL: "Browser (Experimental)",
        BROWSER$SCREENSHOT_ALT: "Browser Screenshot",
        ERROR_TOAST$CLOSE_BUTTON_LABEL: "Close",
        FILE_EXPLORER$UPLOAD: "Upload File",
        FILE_EXPLORER$REFRESH_WORKSPACE: "Refresh workspace",
        FILE_EXPLORER$OPEN_WORKSPACE: "Open workspace",
        FILE_EXPLORER$CLOSE_WORKSPACE: "Close workspace",
        ACTION_MESSAGE$RUN: "Running a bash command",
        ACTION_MESSAGE$RUN_IPYTHON: "Running a Python command",
        ACTION_MESSAGE$READ: "Reading the contents of a file",
        ACTION_MESSAGE$EDIT: "Editing the contents of a file",
        ACTION_MESSAGE$WRITE: "Writing to a file",
        ACTION_MESSAGE$BROWSE: "Browsing the web",
        OBSERVATION_MESSAGE$RUN: "Ran a bash command",
        OBSERVATION_MESSAGE$RUN_IPYTHON: "Ran a Python command",
        OBSERVATION_MESSAGE$READ: "Read the contents of a file",
        OBSERVATION_MESSAGE$EDIT: "Edited the contents of a file",
        OBSERVATION_MESSAGE$WRITE: "Wrote to a file",
        OBSERVATION_MESSAGE$BROWSE: "Browsing completed",
        EXPANDABLE_MESSAGE$SHOW_DETAILS: "Show details",
        EXPANDABLE_MESSAGE$HIDE_DETAILS: "Hide details"
      },
    },
  },
  interpolation: {
    escapeValue: false,
  },
});

const setupStore = (preloadedState?: Partial<RootState>): AppStore =>
  configureStore({
    reducer: rootReducer,
    preloadedState,
  });

// This type interface extends the default options for render from RTL, as well
// as allows the user to specify other things such as initialState, store.
interface ExtendedRenderOptions extends Omit<RenderOptions, "queries"> {
  preloadedState?: Partial<RootState>;
  store?: AppStore;
}

// Export our own customized renderWithProviders function that creates a new Redux store and renders a <Provider>
// Note that this creates a separate Redux store instance for every test, rather than reusing the same store instance and resetting its state
export function renderWithProviders(
  ui: React.ReactElement,
  {
    preloadedState = {},
    // Automatically create a store instance if no store was passed in
    store = setupStore(preloadedState),
    ...renderOptions
  }: ExtendedRenderOptions = {},
) {
  function Wrapper({ children }: PropsWithChildren) {
    return (
      <Provider store={store}>
        <AuthProvider>
          <SettingsUpToDateProvider>
            <QueryClientProvider
              client={
                new QueryClient({
                  defaultOptions: { queries: { retry: false } },
                })
              }
            >
              <ConversationProvider>
                <I18nextProvider i18n={i18n}>{children}</I18nextProvider>
              </ConversationProvider>
            </QueryClientProvider>
          </SettingsUpToDateProvider>
        </AuthProvider>
      </Provider>
    );
  }
  return { store, ...render(ui, { wrapper: Wrapper, ...renderOptions }) };
}
