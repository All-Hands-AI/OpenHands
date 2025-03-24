import { render, screen } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "#/query-client-init";
import { vi, describe, it, expect } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Mock the useJupyter hook
vi.mock("#/hooks/query/use-jupyter", () => ({
  useJupyter: () => ({
    cells: Array(20).fill({
      content: "Test cell content",
      type: "input",
      output: "Test output",
    }),
    isLoading: false,
    appendJupyterInput: vi.fn(),
    appendJupyterOutput: vi.fn(),
    clearJupyter: vi.fn(),
  }),
}));

import { JupyterEditor } from "#/components/features/jupyter/jupyter";

describe("JupyterEditor", () => {
  const mockStore = configureStore({
    reducer: {
      chat: () => ({}),
      agent: () => ({}),
      securityAnalyzer: () => ({}),
    },
    preloadedState: {},
  });

  it("should have a scrollable container", () => {
    // Create a new QueryClient for each test
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
    
    render(
      <QueryClientProvider client={queryClient}>
        <Provider store={mockStore}>
          <div style={{ height: "100vh" }}>
            <JupyterEditor maxWidth={800} />
          </div>
        </Provider>
      </QueryClientProvider>
    );

    const container = screen.getByTestId("jupyter-container");
    expect(container).toHaveClass("flex-1 overflow-y-auto");
  });
});
