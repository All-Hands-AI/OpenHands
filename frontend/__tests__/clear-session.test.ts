import { describe, it, expect, beforeEach, vi } from "vitest";
import { clearSession } from "../src/utils/clear-session";
import store from "../src/store";
import { initialState as browserInitialState } from "../src/state/browserSlice";

describe("clearSession", () => {
  beforeEach(() => {
    // Mock localStorage
    const localStorageMock = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    };
    vi.stubGlobal("localStorage", localStorageMock);

    // Set initial browser state to non-default values
    store.dispatch({
      type: "browser/setUrl",
      payload: "https://example.com",
    });
    store.dispatch({
      type: "browser/setScreenshotSrc",
      payload: "base64screenshot",
    });
  });

  it("should clear localStorage and reset browser state", () => {
    clearSession();

    // Verify localStorage items were removed
    expect(localStorage.removeItem).toHaveBeenCalledWith("token");
    expect(localStorage.removeItem).toHaveBeenCalledWith("repo");

    // Verify browser state was reset
    const state = store.getState();
    expect(state.browser.url).toBe(browserInitialState.url);
    expect(state.browser.screenshotSrc).toBe(browserInitialState.screenshotSrc);
  });
});
