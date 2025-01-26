import { describe, it, expect } from "vitest";
import store from "../src/store";
import {
  setInitialPrompt,
  clearInitialPrompt,
} from "../src/state/initial-query-slice";

describe("Initial Query Behavior", () => {
  it("should clear initial query when clearInitialPrompt is dispatched", () => {
    // Set up initial query in the store
    store.dispatch(setInitialPrompt("test query"));
    expect(store.getState().initialQuery.initialPrompt).toBe("test query");

    // Clear the initial query
    store.dispatch(clearInitialPrompt());

    // Verify initial query is cleared
    expect(store.getState().initialQuery.initialPrompt).toBeNull();
  });
});
