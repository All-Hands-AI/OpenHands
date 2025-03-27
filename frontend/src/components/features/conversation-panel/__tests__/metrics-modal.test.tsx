import React from "react";
import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect } from "vitest";
import { ConversationCard } from "../conversation-card";
import metricsReducer, { MODEL_CONTEXT_SIZES } from "#/state/metrics-slice";

// Mock the formatTimeDelta function
vi.mock("#/utils/format-time-delta", () => ({
  formatTimeDelta: () => "5 minutes",
}));

// Mock posthog
vi.mock("posthog-js", () => ({
  capture: vi.fn(),
}));

describe("Metrics Modal", () => {
  const createStore = (initialState = {}) =>
    configureStore({
      reducer: {
        metrics: metricsReducer,
      },
      preloadedState: {
        metrics: {
          cost: 0.05,
          usage: {
            prompt_tokens: 1000,
            completion_tokens: 500,
            cache_read_tokens: 100,
            cache_write_tokens: 200,
          },
          mostRecentUsage: {
            prompt_tokens: 300,
            completion_tokens: 150,
            cache_read_tokens: 50,
            cache_write_tokens: 100,
          },
          modelName: "claude-3-sonnet-20240229",
          ...initialState,
        },
      },
    });

  it("should display total input and output tokens for the conversation", async () => {
    const store = createStore();

    render(
      <Provider store={store}>
        <ConversationCard
          title="Test Conversation"
          selectedRepository={null}
          lastUpdatedAt={new Date().toISOString()}
          createdAt={new Date().toISOString()}
          showOptions
        />
      </Provider>,
    );

    // Open the metrics modal
    const ellipsisButton = screen.getByTestId("ellipsis-button");
    await userEvent.click(ellipsisButton);

    const displayCostButton = screen.getByTestId("display-cost-button");
    await userEvent.click(displayCostButton);

    // Check if the modal is open
    const modal = screen.getByTestId("metrics-modal");
    expect(modal).toBeInTheDocument();

    // Check if total input tokens are displayed
    expect(screen.getByText("Total Input Tokens:")).toBeInTheDocument();
    expect(screen.getByText("1,000")).toBeInTheDocument();

    // Check if total output tokens are displayed
    expect(screen.getByText("Total Output Tokens:")).toBeInTheDocument();
    expect(screen.getByText("500")).toBeInTheDocument();
  });

  it("should display most recent prompt metrics", async () => {
    const store = createStore();

    render(
      <Provider store={store}>
        <ConversationCard
          title="Test Conversation"
          selectedRepository={null}
          lastUpdatedAt={new Date().toISOString()}
          createdAt={new Date().toISOString()}
          showOptions
        />
      </Provider>,
    );

    // Open the metrics modal
    const ellipsisButton = screen.getByTestId("ellipsis-button");
    await userEvent.click(ellipsisButton);

    const displayCostButton = screen.getByTestId("display-cost-button");
    await userEvent.click(displayCostButton);

    // Check if the most recent prompt section is displayed
    expect(screen.getByText("Most Recent Prompt")).toBeInTheDocument();

    // Check if most recent input tokens are displayed
    const inputTokensElements = screen.getAllByText("Input Tokens:");
    expect(inputTokensElements.length).toBeGreaterThan(0);
    expect(screen.getByText("300")).toBeInTheDocument();

    // Check if most recent output tokens are displayed
    const outputTokensElements = screen.getAllByText("Output Tokens:");
    expect(outputTokensElements.length).toBeGreaterThan(0);
    expect(screen.getByText("150")).toBeInTheDocument();
  });

  it("should display context window usage percentage", async () => {
    const store = createStore();
    const modelName = "claude-3-sonnet-20240229";
    const contextSize = MODEL_CONTEXT_SIZES[modelName];
    const totalTokens = 300 + 150; // prompt_tokens + completion_tokens
    const expectedPercentage = `${((totalTokens / contextSize) * 100).toFixed(2)}%`;

    render(
      <Provider store={store}>
        <ConversationCard
          title="Test Conversation"
          selectedRepository={null}
          lastUpdatedAt={new Date().toISOString()}
          createdAt={new Date().toISOString()}
          showOptions
        />
      </Provider>,
    );

    // Open the metrics modal
    const ellipsisButton = screen.getByTestId("ellipsis-button");
    await userEvent.click(ellipsisButton);

    const displayCostButton = screen.getByTestId("display-cost-button");
    await userEvent.click(displayCostButton);

    // Check if context window usage is displayed
    expect(screen.getByText("Context Window Usage:")).toBeInTheDocument();
    expect(screen.getByText(expectedPercentage)).toBeInTheDocument();
  });
});
