import React from "react";
import { render, act, waitFor } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { ChatMessage } from "#/components/features/chat/chat-message";
import { Provider } from "react-redux";
import configureStore from "redux-mock-store";

const mockStore = configureStore([]);

// Mock the Web Speech API
const mockSpeechSynthesis = {
  cancel: vi.fn(),
  speak: vi.fn(),
  getVoices: vi.fn().mockReturnValue([
    {
      name: "Google US English",
      lang: "en-US",
    },
  ]),
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
  let store;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderWithRedux = (component, speechEnabled = false) => {
    store = mockStore({
      speech: {
        enabled: speechEnabled,
      },
    });
    return render(
      <Provider store={store}>
        {component}
      </Provider>
    );
  };

  it("speaks assistant messages when speech is enabled", async () => {
    await act(async () => {
      renderWithRedux(<ChatMessage type="assistant" message="Hello, world!" />, true);
    });

    await waitFor(() => {
      expect(mockSpeechSynthesis.cancel).toHaveBeenCalled();
      expect(mockSpeechSynthesis.speak).toHaveBeenCalled();
      expect(global.SpeechSynthesisUtterance).toHaveBeenCalledWith("Hello, world!");
    });
  });

  it("does not speak user messages", async () => {
    await act(async () => {
      renderWithRedux(<ChatMessage type="user" message="Hello, world!" />, true);
    });

    await waitFor(() => {
      expect(mockSpeechSynthesis.speak).not.toHaveBeenCalled();
    });
  });

  it("does not speak when speech is disabled", async () => {
    await act(async () => {
      renderWithRedux(<ChatMessage type="assistant" message="Hello, world!" />, false);
    });

    await waitFor(() => {
      expect(mockSpeechSynthesis.speak).not.toHaveBeenCalled();
    });
  });

  it("removes markdown formatting before speaking", async () => {
    await act(async () => {
      renderWithRedux(<ChatMessage type="assistant" message="**Hello** *world* `code`" />, true);
    });

    await waitFor(() => {
      expect(global.SpeechSynthesisUtterance).toHaveBeenCalledWith("**Hello** *world* `code`");
    });
  });
});