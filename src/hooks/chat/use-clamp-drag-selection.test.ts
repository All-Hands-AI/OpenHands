import { renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { useClampDragSelection } from "./use-clamp-drag-selection";

interface Fixture {
  feed: HTMLDivElement;
  message: HTMLParagraphElement;
  headerText: HTMLSpanElement;
  chromeText: HTMLSpanElement;
}

/** Header / feed / composer, matching the chat pane's DOM order. */
function mountChatPane(): Fixture {
  const header = document.createElement("div");
  const headerText = document.createElement("span");
  headerText.textContent = "Conversation name";
  header.append(headerText);

  const feed = document.createElement("div");
  feed.setAttribute("data-testid", "chat-scroll-container");
  const message = document.createElement("p");
  message.textContent = "Local pagination message 100";
  feed.append(message);

  const chrome = document.createElement("div");
  const chromeText = document.createElement("span");
  chromeText.textContent = "Disconnected";
  chrome.append(chromeText);

  document.body.append(header, feed, chrome);
  return { feed, message, headerText, chromeText };
}

/** Drag from `anchor` to `focus`, which is how a mouse drag builds a selection. */
function dragSelection(anchor: Node, focus: Node, focusOffset: number) {
  const selection = window.getSelection()!;
  selection.collapse(anchor, 0);
  selection.extend(focus, focusOffset);
  return selection;
}

function mouseDownOn(target: Element, clientY: number) {
  target.dispatchEvent(
    new MouseEvent("mousedown", { bubbles: true, button: 0, clientY }),
  );
}

function dragPointerTo(clientY: number) {
  document.dispatchEvent(
    new MouseEvent("mousemove", { bubbles: true, clientY }),
  );
  document.dispatchEvent(new Event("selectionchange"));
}

describe("useClampDragSelection", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  afterEach(() => {
    window.getSelection()?.removeAllRanges();
    document.body.innerHTML = "";
  });

  it("keeps the selection in the feed when the drag escapes past the bottom edge", () => {
    const { feed, message, chromeText } = mountChatPane();
    renderHook(() => useClampDragSelection({ current: feed }));

    mouseDownOn(feed, 10);
    const selection = dragSelection(
      message.firstChild!,
      chromeText.firstChild!,
      5,
    );
    expect(feed.contains(selection.focusNode)).toBe(false);

    dragPointerTo(900);

    expect(feed.contains(selection.focusNode)).toBe(true);
    expect(selection.toString()).toContain("Local pagination message 100");
    expect(selection.toString()).not.toContain("Disconnected");
  });

  it("keeps the selection in the feed when the drag escapes past the top edge", () => {
    const { feed, message, headerText } = mountChatPane();
    renderHook(() => useClampDragSelection({ current: feed }));

    mouseDownOn(feed, 400);
    const selection = dragSelection(
      message.firstChild!,
      headerText.firstChild!,
      5,
    );
    expect(feed.contains(selection.focusNode)).toBe(false);

    dragPointerTo(0);

    expect(feed.contains(selection.focusNode)).toBe(true);
    expect(selection.toString()).not.toContain("Conversation name");
  });

  it("keeps the selection stable across repeated clamp updates", () => {
    const { feed, message, chromeText } = mountChatPane();
    renderHook(() => useClampDragSelection({ current: feed }));

    mouseDownOn(feed, 10);
    const selection = dragSelection(
      message.firstChild!,
      chromeText.firstChild!,
      5,
    );

    dragPointerTo(900);
    const afterFirst = selection.toString();
    // The browser keeps emitting updates as the auto-scroll continues; a
    // second clamp must not collapse the range to the container boundary.
    dragPointerTo(900);
    dragPointerTo(900);

    expect(selection.isCollapsed).toBe(false);
    expect(selection.toString()).toBe(afterFirst);
    expect(feed.contains(selection.focusNode)).toBe(true);
  });

  it("does not clamp a selection when the drag started outside the feed", () => {
    const { feed, headerText, chromeText } = mountChatPane();
    renderHook(() => useClampDragSelection({ current: feed }));

    mouseDownOn(chromeText, 10);
    const selection = dragSelection(
      chromeText.firstChild!,
      headerText.firstChild!,
      5,
    );

    dragPointerTo(0);

    expect(feed.contains(selection.focusNode)).toBe(false);
  });

  it("stops clamping once the drag ends", () => {
    const { feed, message, chromeText } = mountChatPane();
    renderHook(() => useClampDragSelection({ current: feed }));

    mouseDownOn(feed, 10);
    document.dispatchEvent(new MouseEvent("mouseup", { bubbles: true }));
    const selection = dragSelection(
      message.firstChild!,
      chromeText.firstChild!,
      5,
    );

    dragPointerTo(900);

    expect(feed.contains(selection.focusNode)).toBe(false);
  });
});
