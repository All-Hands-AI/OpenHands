import { describe, it, expect, beforeEach } from "vitest";
import { speechSlice, toggleSpeech } from "#/state/speech-slice";

// Mock window.speechSynthesis
const mockSpeechSynthesis = {
  cancel: () => {},
};

Object.defineProperty(window, 'speechSynthesis', {
  value: mockSpeechSynthesis,
  writable: true
});

describe("speechSlice", () => {
  const initialState = {
    enabled: false,
  };

  it("should handle initial state", () => {
    expect(speechSlice.reducer(undefined, { type: "unknown" })).toEqual({
      enabled: false,
    });
  });

  it("should handle toggleSpeech", () => {
    const actual = speechSlice.reducer(initialState, toggleSpeech());
    expect(actual.enabled).toEqual(true);

    const actual2 = speechSlice.reducer(actual, toggleSpeech());
    expect(actual2.enabled).toEqual(false);
  });
});