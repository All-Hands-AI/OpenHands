import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { Provider } from "react-redux";
import configureStore from "redux-mock-store";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { ToggleSpeechButton } from "#/components/shared/buttons/toggle-speech-button";
import { toggleSpeech } from "#/state/speech-slice";

const mockStore = configureStore([]);

describe("ToggleSpeechButton", () => {
  let store: any;

  beforeEach(() => {
    store = mockStore({
      speech: {
        enabled: false,
      },
    });
    store.dispatch = vi.fn();
  });

  it("renders correctly when disabled", () => {
    render(
      <Provider store={store}>
        <ToggleSpeechButton />
      </Provider>
    );

    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("title", "Enable speech");
  });

  it("renders correctly when enabled", () => {
    store = mockStore({
      speech: {
        enabled: true,
      },
    });

    render(
      <Provider store={store}>
        <ToggleSpeechButton />
      </Provider>
    );

    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("title", "Disable speech");
  });

  it("dispatches toggle action when clicked", () => {
    render(
      <Provider store={store}>
        <ToggleSpeechButton />
      </Provider>
    );

    const button = screen.getByRole("button");
    fireEvent.click(button);

    expect(store.dispatch).toHaveBeenCalledWith(toggleSpeech());
  });
});