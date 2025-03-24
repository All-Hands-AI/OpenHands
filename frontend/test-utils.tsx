// Test utilities for React components

import React, { PropsWithChildren } from "react";
import { RenderOptions, render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { I18nextProvider, initReactI18next } from "react-i18next";
import i18n from "i18next";
import { vi } from "vitest";
import { AuthProvider } from "#/context/auth-context";
import { ConversationProvider } from "#/context/conversation-context";

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
      translation: {},
    },
  },
  interpolation: {
    escapeValue: false,
  },
});

// Mock store for backward compatibility with tests
const mockStore = {
  getState: vi.fn().mockReturnValue({}),
  dispatch: vi.fn(),
  subscribe: vi.fn(),
};

// This type interface extends the default options for render from RTL
interface ExtendedRenderOptions extends Omit<RenderOptions, "queries"> {
  preloadedState?: Record<string, unknown>;
}

// Export our own customized renderWithProviders function
export function renderWithProviders(
  ui: React.ReactElement,
  {
    preloadedState = {},
    ...renderOptions
  }: ExtendedRenderOptions = {},
) {
  // Create a new QueryClient for each test
  const queryClient = new QueryClient({
    defaultOptions: { 
      queries: { retry: false },
    },
  });
  
  // Set initial query data based on preloadedState
  Object.entries(preloadedState).forEach(([key, value]) => {
    queryClient.setQueryData([key], value);
  });

  function Wrapper({ children }: PropsWithChildren) {
    return (
      <AuthProvider initialGithubTokenIsSet>
        <QueryClientProvider client={queryClient}>
          <ConversationProvider>
            <I18nextProvider i18n={i18n}>{children}</I18nextProvider>
          </ConversationProvider>
        </QueryClientProvider>
      </AuthProvider>
    );
  }
  
  return { 
    store: mockStore, // For backward compatibility
    queryClient,
    ...render(ui, { wrapper: Wrapper, ...renderOptions }) 
  };
}
