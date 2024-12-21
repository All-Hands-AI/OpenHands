import { describe, it, expect } from "vitest";
import store from "../src/store";
import {
  setInitialQuery,
  clearInitialQuery,
} from "../src/state/initial-query-slice";

describe("Initial Query Behavior", () => {
  it("should clear initial query when clearInitialQuery is dispatched", () => {
    // Set up initial query in the store
    store.dispatch(setInitialQuery("test query"));
    expect(store.getState().initialQuery.initialQuery).toBe("test query");

    // Clear the initial query
    store.dispatch(clearInitialQuery());

    // Verify initial query is cleared
    expect(store.getState().initialQuery.initialQuery).toBeNull();
  });
});
