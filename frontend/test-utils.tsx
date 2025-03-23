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

// Mock react-router components for testing
vi.mock("react-router", async () => {
  const actual =
    await vi.importActual<typeof import("react-router")>("react-router");
  return {
    ...actual,
    useParams: () => ({ conversationId: "test-conversation-id" }),
    RouterProvider: ({ router }: { router?: any }) => {
      if (router?.routes?.[0]?.element) {
        return router.routes[0].element;
      }
      return <div>Mocked Router</div>;
    }
  };
});

// Mock react-router/dist/development/dom-export to fix SSR errors
vi.mock("react-router/dist/development/dom-export", () => {
  return {
    createHydratedRouter: () => ({
      routes: [{ element: <div>Mocked Router</div> }]
    }),
    HydratedRouter: ({ children }: { children?: React.ReactNode }) => <>{children || <div>Mocked Router</div>}</>,
    RouterProvider: ({ router, children }: { router?: any, children?: React.ReactNode }) => {
      return <>{children || (router?.routes?.[0]?.element || <div>Mocked Router</div>)}</>;
    }
  };
});

// Mock the metrics hook
vi.mock("#/hooks/query/use-metrics", () => ({
  useMetrics: () => ({
    metrics: {
      cost: 0.123,
      usage: {
        prompt_tokens: 100,
        completion_tokens: 200,
        total_tokens: 300
      }
    },
    updateMetrics: vi.fn()
  })
}));

// Mock the status hook
vi.mock("#/hooks/query/use-status", () => ({
  useStatus: () => ({
    status: {
      runtimeActive: true,
      runtimeConnected: true,
      runtimeStatus: "connected",
      runtimeVersion: "1.0.0",
      wsConnected: true,
    },
    updateStatus: vi.fn()
  })
}));

// Initialize i18n for tests
i18n.use(initReactI18next).init({
  lng: "en",
  fallbackLng: "en",
  ns: ["translation"],
  defaultNS: "translation",
  resources: {
    en: {
      translation: {},
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

// Create a query client for testing
const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      cacheTime: 0,
      staleTime: 0,
    },
  },
  logger: {
    log: console.log,
    warn: console.warn,
    error: () => {},
  },
});

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
        <AuthProvider initialGithubTokenIsSet>
          <QueryClientProvider client={createTestQueryClient()}>
            <ConversationProvider>
              <I18nextProvider i18n={i18n}>
                {children}
              </I18nextProvider>
            </ConversationProvider>
          </QueryClientProvider>
        </AuthProvider>
      </Provider>
    );
  }
  
  return { store, ...render(ui, { wrapper: Wrapper, ...renderOptions }) };
}
