import { describe, it, expect, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook } from "@testing-library/react";
import React from "react";
import { useInitialQuery } from "../src/hooks/query/use-initial-query";

// Mock the query-redux-bridge
vi.mock("../src/utils/query-redux-bridge", () => ({
  getQueryReduxBridge: vi.fn(() => ({
    getReduxSliceState: vi.fn(() => ({
      files: [],
      initialPrompt: null,
      selectedRepository: null,
    })),
  })),
}));

// Create a wrapper with QueryClientProvider
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe("Initial Query Behavior", () => {
  it("should have initial state", () => {
    const { result } = renderHook(() => useInitialQuery(), {
      wrapper: createWrapper(),
    });
    
    // Verify initial state
    expect(result.current.files).toEqual([]);
    expect(result.current.initialPrompt).toBeNull();
    expect(result.current.selectedRepository).toBeNull();
  });
});
