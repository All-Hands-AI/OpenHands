import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { handleObservationMessage } from "#/services/observations";
import { setScreenshotSrc, setUrl } from "#/state/browser-slice";
import ObservationType from "#/types/observation-type";

// Mock the store
const mockDispatch = vi.fn();
vi.mock("#/store", () => ({
  default: {
    dispatch: mockDispatch,
  },
}));

describe("handleObservationMessage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it("updates browser state when receiving a browse observation", () => {
    const message = {
      id: "test-id",
      cause: "test-cause",
      observation: ObservationType.BROWSE,
      content: "test content",
      message: "test message",
      extras: {
        url: "https://example.com",
        screenshot: "base64-screenshot-data",
      },
    };

    handleObservationMessage(message);

    // Check that setScreenshotSrc and setUrl were called with the correct values
    expect(mockDispatch).toHaveBeenCalledWith(setScreenshotSrc("base64-screenshot-data"));
    expect(mockDispatch).toHaveBeenCalledWith(setUrl("https://example.com"));
  });

  it("updates browser state when receiving a browse_interactive observation", () => {
    const message = {
      id: "test-id",
      cause: "test-cause",
      observation: ObservationType.BROWSE_INTERACTIVE,
      content: "test content",
      message: "test message",
      extras: {
        url: "https://example.com",
        screenshot: "base64-screenshot-data",
      },
    };

    handleObservationMessage(message);

    // Check that setScreenshotSrc and setUrl were called with the correct values
    expect(mockDispatch).toHaveBeenCalledWith(setScreenshotSrc("base64-screenshot-data"));
    expect(mockDispatch).toHaveBeenCalledWith(setUrl("https://example.com"));
  });
});