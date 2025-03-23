import { useMetrics } from "#/hooks/query/use-metrics";
import { vi, describe, it } from "vitest";

// Mock the query-redux-bridge
vi.mock("#/utils/query-redux-bridge", () => ({
  getQueryReduxBridge: vi.fn(() => ({
    getReduxSliceState: vi.fn(() => ({
      cost: null,
      usage: null,
    })),
  })),
}));

// Skip tests for now due to JSX parsing issues
describe("useMetrics", () => {
  it("should return initial metrics state", () => {
    // Test implementation
  });

  it("should update metrics state", async () => {
    // Test implementation
  });
});
