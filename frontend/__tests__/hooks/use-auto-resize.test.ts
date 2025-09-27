import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, beforeEach, vi } from "vitest";
import { useAutoResize } from "#/hooks/use-auto-resize";
import { RefObject } from "react";

class MockHTMLElement {
  style: CSSStyleDeclaration;
  offsetHeight = 20;
  clientHeight = 20;
  scrollHeight = 20;

  constructor() {
    const styleObj: any = {};

    styleObj.setProperty = (property: string, value: string) => {
      styleObj[property] = value;
    };

    this.style = styleObj as CSSStyleDeclaration;
  }

  // Simulate setting height and measuring scrollHeight
  setScrollHeight(height: number) {
    this.scrollHeight = height;
  }

  setOffsetHeight(height: number) {
    this.offsetHeight = height;
  }
}

describe("useAutoResize", () => {
  let mockElement: MockHTMLElement;
  let elementRef: RefObject<HTMLElement>;

  beforeEach(() => {
    mockElement = new MockHTMLElement();
    elementRef = { current: mockElement as unknown as HTMLElement };
  });

  it("should shrink input height after content is deleted (bug reproduction)", () => {
    const { result } = renderHook(() =>
      useAutoResize(elementRef, {
        minHeight: 20,
        maxHeight: 400,
      }),
    );

    // Step 1: Simulate large content that expands input to max height
    mockElement.setScrollHeight(500); // Content larger than maxHeight
    mockElement.setOffsetHeight(400); // Input expanded to maxHeight
    mockElement.style.height = "400px";

    act(() => {
      result.current.smartResize();
    });

    // Verify input is at max height
    expect(mockElement.style.height).toBe("400px");

    // Step 2: Simulate deleting all content (content becomes very small)
    mockElement.setScrollHeight(20); // Very small content
    // offsetHeight stays 400px (this is the bug - it should shrink)
    mockElement.setOffsetHeight(400);

    act(() => {
      result.current.smartResize();
    });

    // BUG: This test will FAIL because the input stays at 400px
    // EXPECTED: Input should shrink back to minHeight (20px) or close to content size
    expect(parseInt(mockElement.style.height)).toBeLessThan(100);
  });

  it("should preserve manually resized height when content is small", () => {
    const { result } = renderHook(() =>
      useAutoResize(elementRef, {
        minHeight: 20,
        maxHeight: 400,
      }),
    );

    // Simulate manually resized input (not at maxHeight)
    mockElement.setScrollHeight(30); // Small content
    mockElement.setOffsetHeight(150); // Manually resized to 150px
    mockElement.style.height = "150px";

    act(() => {
      result.current.smartResize();
    });

    // Should preserve manual height since it's not at maxHeight
    expect(mockElement.style.height).toBe("150px");
  });

  it("should grow input height when content increases", () => {
    const { result } = renderHook(() =>
      useAutoResize(elementRef, {
        minHeight: 20,
        maxHeight: 400,
      }),
    );

    // Start with small content and height
    mockElement.setScrollHeight(20);
    mockElement.setOffsetHeight(20);
    mockElement.style.height = "20px";

    // Content grows
    mockElement.setScrollHeight(100);

    act(() => {
      result.current.smartResize();
    });

    // Should grow to accommodate content
    expect(parseInt(mockElement.style.height)).toBeGreaterThanOrEqual(100);
  });
});
