import React from "react";
import { render } from "@testing-library/react";
import { Provider } from "react-redux";
import configureStore from "redux-mock-store";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { ChatMessage } from "#/components/features/chat/chat-message";

const mockStore = configureStore([]);

// Mock the Web Speech API
const mockSpeechSynthesis = {
  cancel: vi.fn(),
  speak: vi.fn(),
  getVoices: vi.fn().mockReturnValue([]),
};

const mockUtterance = {
  voice: null,
  rate: 1,
  pitch: 1,
  volume: 1,
};

// @ts-ignore - partial implementation
global.SpeechSynthesisUtterance = vi.fn().mockImplementation(() => mockUtterance);
// @ts-ignore - partial implementation
global.speechSynthesis = mockSpeechSynthesis;

describe("ChatMessage with speech", () => {
  let store: any;

  beforeEach(() => {
    store = mockStore({
      speech: {
        enabled: true,
      },
    });
    vi.clearAllMocks();
  });

  it("speaks assistant messages when speech is enabled", () => {
    render(
      <Provider store={store}>
        <ChatMessage type="assistant" message="Hello, world!" />
      </Provider>
    );

    expect(mockSpeechSynthesis.cancel).toHaveBeenCalled();
    expect(mockSpeechSynthesis.speak).toHaveBeenCalled();
    expect(global.SpeechSynthesisUtterance).toHaveBeenCalledWith("Hello, world!");
  });

  it("does not speak user messages", () => {
    render(
      <Provider store={store}>
        <ChatMessage type="user" message="Hello, world!" />
      </Provider>
    );

    expect(mockSpeechSynthesis.speak).not.toHaveBeenCalled();
  });

  it("does not speak when speech is disabled", () => {
    store = mockStore({
      speech: {
        enabled: false,
      },
    });

    render(
      <Provider store={store}>
        <ChatMessage type="assistant" message="Hello, world!" />
      </Provider>
    );

    expect(mockSpeechSynthesis.speak).not.toHaveBeenCalled();
  });

  it("removes markdown formatting before speaking", () => {
    render(
      <Provider store={store}>
        <ChatMessage type="assistant" message="**Hello** *world* `code`" />
      </Provider>
    );

    expect(global.SpeechSynthesisUtterance).toHaveBeenCalledWith("Hello world code");
  });
});