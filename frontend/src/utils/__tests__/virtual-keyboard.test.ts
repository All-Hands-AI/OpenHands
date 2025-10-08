import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  getVirtualKeyboardManager,
  cleanupVirtualKeyboardManager,
} from "../utils";

// Mock navigator.virtualKeyboard
const mockVirtualKeyboard = {
  overlaysContent: false,
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  boundingRect: { height: 0 },
};

// Mock navigator
Object.defineProperty(global, "navigator", {
  value: {
    virtualKeyboard: mockVirtualKeyboard,
  },
  writable: true,
});

describe("VirtualKeyboardManager", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset the mock state
    mockVirtualKeyboard.overlaysContent = false;
    mockVirtualKeyboard.boundingRect = { height: 0 };
  });

  afterEach(() => {
    cleanupVirtualKeyboardManager();
  });

  it("should initialize with overlaysContent set to true", () => {
    getVirtualKeyboardManager();

    expect(mockVirtualKeyboard.overlaysContent).toBe(true);
    expect(mockVirtualKeyboard.addEventListener).toHaveBeenCalledWith(
      "geometrychange",
      expect.any(Function),
    );
  });

  it("should return false when keyboard is not visible", () => {
    const manager = getVirtualKeyboardManager();

    expect(manager.isKeyboardVisible()).toBe(false);
  });

  it("should return true when keyboard is visible", () => {
    const manager = getVirtualKeyboardManager();

    // Simulate keyboard becoming visible
    mockVirtualKeyboard.boundingRect = { height: 200 };

    // Trigger the geometry change event
    const geometryChangeHandler =
      mockVirtualKeyboard.addEventListener.mock.calls[0][1];
    geometryChangeHandler({ target: { boundingRect: { height: 200 } } });

    expect(manager.isKeyboardVisible()).toBe(true);
  });

  it("should notify listeners when keyboard visibility changes", () => {
    const manager = getVirtualKeyboardManager();
    const listener = vi.fn();

    const removeListener = manager.addListener(listener);

    // Simulate keyboard appearing
    const geometryChangeHandler =
      mockVirtualKeyboard.addEventListener.mock.calls[0][1];
    geometryChangeHandler({ target: { boundingRect: { height: 200 } } });

    expect(listener).toHaveBeenCalledTimes(1);

    // Simulate keyboard disappearing
    geometryChangeHandler({ target: { boundingRect: { height: 0 } } });

    expect(listener).toHaveBeenCalledTimes(2);

    // Test listener removal
    removeListener();
    geometryChangeHandler({ target: { boundingRect: { height: 200 } } });

    expect(listener).toHaveBeenCalledTimes(2); // Should not be called again
  });

  it("should handle cleanup properly", () => {
    const manager = getVirtualKeyboardManager();
    const listener = vi.fn();

    manager.addListener(listener);
    manager.destroy();

    // Should not throw errors after destruction
    expect(() => manager.isKeyboardVisible()).not.toThrow();
    expect(() => manager.addListener(listener)).not.toThrow();
  });

  it("should handle missing virtual keyboard API gracefully", () => {
    // Remove virtual keyboard from navigator
    Object.defineProperty(global, "navigator", {
      value: {},
      writable: true,
    });

    cleanupVirtualKeyboardManager();

    const manager = getVirtualKeyboardManager();
    expect(manager.isKeyboardVisible()).toBe(false);
  });
});
