import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { I18nextProvider } from "react-i18next";
import { vi, describe, it, beforeEach, expect } from "vitest";
import { ActionSuggestions } from "./action-suggestions";
import { AgentState } from "#/types/agent-state";
import i18n from "#/i18n";

// Mock the hooks
vi.mock("#/hooks/use-user-providers", () => ({
  useUserProviders: () => ({ providers: [] }),
}));

vi.mock("#/hooks/query/use-active-conversation", () => ({
  useActiveConversation: () => ({ data: null }),
}));

// Mock posthog
vi.mock("posthog-js", () => ({
  capture: vi.fn(),
}));

const createMockStore = () =>
  configureStore({
    reducer: {
      // Add minimal reducers needed for the test
      agent: (state = {}) => state,
    },
  });

const createWrapper = () => {
  const store = createMockStore();
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  function TestWrapper({ children }: { children: React.ReactNode }) {
    return (
      <Provider store={store}>
        <QueryClientProvider client={queryClient}>
          <I18nextProvider i18n={i18n}>{children}</I18nextProvider>
        </QueryClientProvider>
      </Provider>
    );
  }

  return TestWrapper;
};

describe("ActionSuggestions", () => {
  const mockOnSuggestionsClick = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows Continue button when agent is rate limited", () => {
    const Wrapper = createWrapper();

    render(
      <Wrapper>
        <ActionSuggestions
          onSuggestionsClick={mockOnSuggestionsClick}
          agentState={AgentState.RATE_LIMITED}
        />
      </Wrapper>,
    );

    expect(screen.getByText("ACTION$CONTINUE")).toBeInTheDocument();
  });

  it("does not show Continue button when agent is not rate limited", () => {
    const Wrapper = createWrapper();

    render(
      <Wrapper>
        <ActionSuggestions
          onSuggestionsClick={mockOnSuggestionsClick}
          agentState={AgentState.AWAITING_USER_INPUT}
        />
      </Wrapper>,
    );

    expect(screen.queryByText("ACTION$CONTINUE")).not.toBeInTheDocument();
  });

  it("does not show git buttons when agent is rate limited", () => {
    const Wrapper = createWrapper();

    render(
      <Wrapper>
        <ActionSuggestions
          onSuggestionsClick={mockOnSuggestionsClick}
          agentState={AgentState.RATE_LIMITED}
        />
      </Wrapper>,
    );

    expect(screen.queryByText("Push to Branch")).not.toBeInTheDocument();
    expect(screen.queryByText("Push & Create PR")).not.toBeInTheDocument();
  });
});
