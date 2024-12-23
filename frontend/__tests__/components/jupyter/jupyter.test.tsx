import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import { JupyterEditor } from "#/components/features/jupyter/jupyter";
import { jupyterReducer } from "#/state/jupyter-slice";
import { vi, describe, it, expect } from "vitest";

describe("JupyterEditor", () => {
  const mockStore = configureStore({
    reducer: {
      fileState: () => ({}),
      initalQuery: () => ({}),
      browser: () => ({}),
      chat: () => ({}),
      code: () => ({}),
      cmd: () => ({}),
      agent: () => ({}),
      jupyter: jupyterReducer,
      securityAnalyzer: () => ({}),
      status: () => ({}),
    },
    preloadedState: {
      jupyter: {
        cells: Array(20).fill({
          content: "Test cell content",
          type: "input",
          output: "Test output",
        }),
      },
    },
  });

  it("should have a scrollable container", () => {
    render(
      <Provider store={mockStore}>
        <div style={{ height: "100vh" }}>
          <JupyterEditor maxWidth={800} />
        </div>
      </Provider>
    );

    const container = screen.getByTestId("jupyter-container");
    expect(container).toHaveClass("flex-1 overflow-y-auto");
  });
});
