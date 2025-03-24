// Test utilities for React components

import React, { PropsWithChildren } from "react";
import { RenderOptions, render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { I18nextProvider, initReactI18next } from "react-i18next";
import i18n from "i18next";
import { vi } from "vitest";
import { AuthProvider } from "#/context/auth-context";
import { ConversationProvider } from "#/context/conversation-context";
import { initQueryClientWrapper } from "#/utils/query-client-wrapper";

// Mock the QueryClientWrapper module
vi.mock("#/utils/query-client-wrapper", async (importOriginal) => {
  const actual = await importOriginal<typeof import("#/utils/query-client-wrapper")>();
  
  // Create a mock QueryClientWrapper class
  const mockWrapper = {
    updateQueryData: vi.fn(),
    getQueryData: vi.fn(),
    invalidateQuery: vi.fn(),
    resetQuery: vi.fn(),
    getSliceState: vi.fn(),
    setQueryData: vi.fn(),
  };
  
  // Return the original module with mocked functions
  return {
    ...actual,
    initQueryClientWrapper: vi.fn(() => mockWrapper),
    getQueryClientWrapper: vi.fn(() => mockWrapper),
  };
});

// Mock the hooks that use QueryReduxBridge
vi.mock("#/hooks/query/use-initial-query", async (importOriginal) => {
  const actual = await importOriginal<typeof import("#/hooks/query/use-initial-query")>();
  return {
    ...actual,
    useInitialQuery: vi.fn(() => ({
      files: [],
      initialPrompt: null,
      selectedRepository: null,
      isLoading: false,
      addFile: vi.fn(),
      removeFile: vi.fn(),
      clearFiles: vi.fn(),
      setInitialPrompt: vi.fn(),
      clearInitialPrompt: vi.fn(),
      setSelectedRepository: vi.fn(),
      clearSelectedRepository: vi.fn(),
    })),
  };
});

vi.mock("#/hooks/query/use-browser", async (importOriginal) => {
  const actual = await importOriginal<typeof import("#/hooks/query/use-browser")>();
  return {
    ...actual,
    useBrowser: vi.fn(() => ({
      url: "https://github.com/All-Hands-AI/OpenHands",
      screenshotSrc: "",
      isLoading: false,
      setUrl: vi.fn(),
      setScreenshotSrc: vi.fn(),
    })),
  };
});

vi.mock("#/hooks/query/use-command", async (importOriginal) => {
  const actual = await importOriginal<typeof import("#/hooks/query/use-command")>();
  return {
    ...actual,
    useCommand: vi.fn(() => ({
      commands: [],
      isLoading: false,
      appendInput: vi.fn(),
      appendOutput: vi.fn(),
      clearTerminal: vi.fn(),
    })),
  };
});

vi.mock("#/hooks/query/use-jupyter", async (importOriginal) => {
  const actual = await importOriginal<typeof import("#/hooks/query/use-jupyter")>();
  return {
    ...actual,
    useJupyter: vi.fn(() => ({
      cells: [],
      isLoading: false,
      appendCell: vi.fn(),
      clearJupyter: vi.fn(),
    })),
  };
});

vi.mock("#/hooks/query/use-security-analyzer", async (importOriginal) => {
  const actual = await importOriginal<typeof import("#/hooks/query/use-security-analyzer")>();
  return {
    ...actual,
    useSecurityAnalyzer: vi.fn(() => ({
      securityAnalyzerResults: null,
      isLoading: false,
      setSecurityAnalyzerResults: vi.fn(),
      clearSecurityAnalyzerResults: vi.fn(),
    })),
  };
});

vi.mock("#/hooks/query/use-status-message", async (importOriginal) => {
  const actual = await importOriginal<typeof import("#/hooks/query/use-status-message")>();
  return {
    ...actual,
    useStatusMessage: vi.fn(() => ({
      statusMessage: {
        id: "status.ready",
        message: "Ready",
        type: "info",
        status_update: true
      },
      isLoading: false,
      setStatusMessage: vi.fn(),
      clearStatusMessage: vi.fn(),
    })),
  };
});

vi.mock("#/hooks/query/use-metrics", async (importOriginal) => {
  const actual = await importOriginal<typeof import("#/hooks/query/use-metrics")>();
  return {
    ...actual,
    useMetrics: vi.fn(() => ({
      metrics: {
        cost: 0.05,
        usage: {
          prompt_tokens: 100,
          completion_tokens: 50,
          total_tokens: 150,
        }
      },
      isLoading: false,
      setMetrics: vi.fn(),
      clearMetrics: vi.fn(),
    })),
  };
});

vi.mock("#/hooks/query/use-agent-state", async (importOriginal) => {
  const actual = await importOriginal<typeof import("#/hooks/query/use-agent-state")>();
  
  // Import the AgentState enum to use the correct value
  const { AgentState } = await import("#/types/agent-state");
  
  return {
    ...actual,
    useAgentState: vi.fn(() => ({
      curAgentState: AgentState.LOADING,
      isLoading: false,
      setAgentState: vi.fn(),
    })),
  };
});

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
