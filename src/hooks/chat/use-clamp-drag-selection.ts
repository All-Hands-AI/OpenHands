import React from "react";

/**
 * Keeps a drag-selection inside the message feed.
 *
 * The feed is a scrollable sibling of the pane header and the composer/footer.
 * When a drag reaches the feed edge and the feed auto-scrolls, the browser
 * hit-tests the nearest selectable node and extends the range outside the feed
 * — to the pane header when dragging up, or to the composer/footer when
 * dragging down — so the selection focus escapes the message list.
 *
 * While a primary-button drag that started inside the feed is in progress, any
 * selection whose focus leaves the feed is pulled back to the feed edge nearest
 * the pointer. The selection anchor is preserved, so the range grows to the
 * first/last message instead of the layout edge. Selection elsewhere is
 * untouched because the clamp only engages for drags that begin inside the
 * feed.
 */
export function useClampDragSelection(
  containerRef: React.RefObject<HTMLElement | null>,
) {
  React.useEffect(() => {
    const container = containerRef.current;
    if (!container) return undefined;

    let dragging = false;
    let pointerY: number | null = null;
    // The browser's drag anchor (where the drag started). Captured once and
    // kept, because clamping the selection rewrites it and re-reading the
    // rewritten value would collapse the range on the next update.
    let dragAnchor: { node: Node; offset: number } | null = null;

    const onMouseDown = (event: MouseEvent) => {
      if (event.button !== 0) return;
      if (!container.contains(event.target as Node)) return;
      dragging = true;
      pointerY = event.clientY;
      dragAnchor = null;
    };

    const onMouseMove = (event: MouseEvent) => {
      if (dragging) pointerY = event.clientY;
    };

    const end = () => {
      dragging = false;
      pointerY = null;
      dragAnchor = null;
    };

    const clampSelection = () => {
      if (!dragging) return;
      const selection = window.getSelection();
      if (!selection || selection.rangeCount === 0 || selection.isCollapsed) {
        return;
      }
      const { anchorNode, focusNode } = selection;
      // Only drags that started inside the feed are clamped.
      if (!anchorNode || !container.contains(anchorNode)) return;

      if (!dragAnchor) {
        dragAnchor = { node: anchorNode, offset: selection.anchorOffset };
      }
      if (focusNode && container.contains(focusNode)) return;

      const bounds = container.getBoundingClientRect();
      const below = pointerY === null || pointerY >= bounds.bottom;
      const range = document.createRange();
      if (below) {
        range.setStart(dragAnchor.node, dragAnchor.offset);
        range.setEnd(container, container.childNodes.length);
      } else {
        range.setStart(container, 0);
        range.setEnd(dragAnchor.node, dragAnchor.offset);
      }
      selection.removeAllRanges();
      selection.addRange(range);
    };

    // Capture phase so the drag is tracked before any handler stops propagation.
    document.addEventListener("mousedown", onMouseDown, true);
    document.addEventListener("mousemove", onMouseMove, true);
    document.addEventListener("mouseup", end, true);
    document.addEventListener("pointerup", end, true);
    document.addEventListener("pointercancel", end, true);
    document.addEventListener("selectionchange", clampSelection);
    window.addEventListener("blur", end);
    return () => {
      document.removeEventListener("mousedown", onMouseDown, true);
      document.removeEventListener("mousemove", onMouseMove, true);
      document.removeEventListener("mouseup", end, true);
      document.removeEventListener("pointerup", end, true);
      document.removeEventListener("pointercancel", end, true);
      document.removeEventListener("selectionchange", clampSelection);
      window.removeEventListener("blur", end);
    };
  }, [containerRef]);
}
