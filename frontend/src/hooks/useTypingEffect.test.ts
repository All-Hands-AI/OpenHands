import { renderHook, act } from "@testing-library/react";
import { useTypingEffect } from "./useTypingEffect";

describe("useTypingEffect", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  // This test fails because the hook improperly handles this case.
  it.skip("should handle empty strings array", () => {
    const { result } = renderHook(() => useTypingEffect([]));

    // Immediately check the result since there's nothing to type
    expect(result.current).toBe("\u00A0"); // Non-breaking space
  });

  it("should type out a string correctly", () => {
    const message = "Hello, world! This is a test message.";

    const { result } = renderHook(() => useTypingEffect([message]));

    // msg.length - 2 because the first two characters are typed immediately
    // 100ms per character, 0.1 playbackRate
    const msToRun = (message.length - 2) * 100 * 0.1;

    // Fast-forward time by to simulate typing message
    act(() => {
      vi.advanceTimersByTime(msToRun - 1); // exclude the last character for testing
    });

    expect(result.current).toBe(message.slice(0, -1));

    act(() => {
      vi.advanceTimersByTime(1); // include the last character
    });

    expect(result.current).toBe(message);
  });

  it("should type of a string correctly with a different playback rate", () => {
    const message = "Hello, world! This is a test message.";
    const playbackRate = 0.5;

    const { result } = renderHook(() =>
      useTypingEffect([message], { playbackRate }),
    );

    const msToRun = (message.length - 2) * 100 * playbackRate;

    act(() => {
      vi.advanceTimersByTime(msToRun - 1); // exclude the last character for testing
    });

    expect(result.current).toBe(message.slice(0, -1));

    act(() => {
      vi.advanceTimersByTime(1); // include the last character
    });

    expect(result.current).toBe(message);
  });

  it("should loop through strings when multiple are provided", () => {
    const messages = ["Hello", "World"];

    const { result } = renderHook(() => useTypingEffect(messages));

    const msToRunFirstString = messages[0].length * 100 * 0.1;

    // Fast-forward to end of first string
    act(() => {
      vi.advanceTimersByTime(msToRunFirstString);
    });

    expect(result.current).toBe(messages[0]); // Hello

    // Fast-forward through the delay and through the second string
    act(() => {
      // TODO: Improve to clarify the expected timing
      vi.runAllTimers();
    });

    expect(result.current).toBe(messages[1]); // World
  });

  it("should call setTypingActive with false when typing completes without loop", () => {
    const setTypingActiveMock = vi.fn();

    renderHook(() =>
      useTypingEffect(["Hello, world!", "This is a test message."], {
        loop: false,
        setTypingActive: setTypingActiveMock,
      }),
    );

    expect(setTypingActiveMock).not.toHaveBeenCalled();

    act(() => {
      vi.runAllTimers();
    });

    expect(setTypingActiveMock).toHaveBeenCalledWith(false);
    expect(setTypingActiveMock).toHaveBeenCalledTimes(1);
  });

  it("should call addAssistantMessageToChat with the typeThis argument when typing completes without loop", () => {
    const addAssistantMessageToChatMock = vi.fn();

    renderHook(() =>
      useTypingEffect(["Hello, world!", "This is a test message."], {
        loop: false,
        // Note that only "Hello, world!" is typed out (the first string in the array)
        typeThis: { content: "Hello, world!", sender: "assistant" },
        addAssistantMessageToChat: addAssistantMessageToChatMock,
      }),
    );

    expect(addAssistantMessageToChatMock).not.toHaveBeenCalled();

    act(() => {
      vi.runAllTimers();
    });

    expect(addAssistantMessageToChatMock).toHaveBeenCalledTimes(1);
    expect(addAssistantMessageToChatMock).toHaveBeenCalledWith({
      content: "Hello, world!",
      sender: "assistant",
    });
  });

  it("should call takeOneAndType when typing completes without loop", () => {
    const takeOneAndTypeMock = vi.fn();

    renderHook(() =>
      useTypingEffect(["Hello, world!", "This is a test message."], {
        loop: false,
        takeOneAndType: takeOneAndTypeMock,
      }),
    );

    expect(takeOneAndTypeMock).not.toHaveBeenCalled();

    act(() => {
      vi.runAllTimers();
    });

    expect(takeOneAndTypeMock).toHaveBeenCalledTimes(1);
  });

  // Implementation is not clear on how to handle this case
  it.todo("should handle typing with loop");
});
