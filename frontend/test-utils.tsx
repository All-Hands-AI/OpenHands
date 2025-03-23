// Test utilities for rendering components with providers

import React, { PropsWithChildren } from "react";
import { RenderOptions, render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { I18nextProvider, initReactI18next } from "react-i18next";
import i18n from "i18next";
import { vi } from "vitest";
import { AuthProvider } from "#/context/auth-context";
import { ConversationProvider } from "#/context/conversation-context";
import { ChatProvider } from "#/context/chat-context";
import { TerminalProvider } from "#/context/terminal-context";
import { BrowserProvider } from "#/context/browser-context";
import { AgentStateProvider } from "#/context/agent-state-context";
import { FileStateProvider } from "#/context/file-state-context";

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

// This type interface extends the default options for render from RTL
interface ExtendedRenderOptions extends Omit<RenderOptions, "queries"> {}

// Export our own customized renderWithProviders function that sets up all the necessary providers
export function renderWithProviders(
  ui: React.ReactElement,
  renderOptions: ExtendedRenderOptions = {},
) {
  function Wrapper({ children }: PropsWithChildren) {
    return (
      <AuthProvider initialGithubTokenIsSet>
        <QueryClientProvider
          client={
            new QueryClient({
              defaultOptions: { queries: { retry: false } },
            })
          }
        >
          <ConversationProvider>
            <AgentStateProvider>
              <ChatProvider>
                <TerminalProvider>
                  <BrowserProvider>
                    <FileStateProvider>
                      <I18nextProvider i18n={i18n}>{children}</I18nextProvider>
                    </FileStateProvider>
                  </BrowserProvider>
                </TerminalProvider>
              </ChatProvider>
            </AgentStateProvider>
          </ConversationProvider>
        </QueryClientProvider>
      </AuthProvider>
    );
  }
  return { ...render(ui, { wrapper: Wrapper, ...renderOptions }) };
}
