import { act, renderHook } from "@testing-library/react";
import useInputComposition from "./useInputComposition";

describe("useInputComposition", () => {
  it("should return isComposing as false by default", () => {
    const { result } = renderHook(() => useInputComposition());
    expect(result.current.isComposing).toBe(false);
  });

  it("should set isComposing to true when onCompositionStart is called", () => {
    const { result } = renderHook(() => useInputComposition());

    act(() => {
      result.current.onCompositionStart();
    });

    expect(result.current.isComposing).toBe(true);
  });

  it("should set isComposing to false when onCompositionEnd is called", () => {
    const { result } = renderHook(() => useInputComposition());

    act(() => {
      result.current.onCompositionStart();
    });

    expect(result.current.isComposing).toBe(true);

    act(() => {
      result.current.onCompositionEnd();
    });

    expect(result.current.isComposing).toBe(false);
  });
});
