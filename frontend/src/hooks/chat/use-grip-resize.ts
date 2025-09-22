import { useRef, useState, useCallback } from "react";
import { useDispatch } from "react-redux";
import { useAutoResize } from "#/hooks/use-auto-resize";
import {
  IMessageToSend,
  setShouldHideSuggestions,
} from "#/state/conversation-slice";
import { CHAT_INPUT } from "#/utils/constants";

/**
 * Hook for managing grip resize functionality
 */
export const useGripResize = (
  chatInputRef: React.RefObject<HTMLDivElement | null>,
  messageToSend: IMessageToSend | null,
) => {
  const gripRef = useRef<HTMLDivElement | null>(null);

  const [isGripVisible, setIsGripVisible] = useState(false);

  const dispatch = useDispatch();

  // Drag state management callbacks
  const handleDragStart = useCallback(() => {
    // Keep grip visible during drag by adding a CSS class
    if (gripRef.current) {
      gripRef.current.classList.add("opacity-100");
      gripRef.current.classList.remove("opacity-0");
    }
  }, []);

  const handleDragEnd = useCallback(() => {
    // Restore hover-based visibility
    if (gripRef.current) {
      gripRef.current.classList.remove("opacity-100");
      gripRef.current.classList.add("opacity-0");
    }
  }, []);

  // Handle click on top edge area to toggle grip visibility
  const handleTopEdgeClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setIsGripVisible((prev) => !prev);
  }, []);

  // Callback to handle height changes and manage suggestions visibility
  const handleHeightChange = useCallback(
    (height: number) => {
      // Hide suggestions when input height exceeds the threshold
      const shouldHideChatSuggestions = height > CHAT_INPUT.HEIGHT_THRESHOLD;
      dispatch(setShouldHideSuggestions(shouldHideChatSuggestions));
    },
    [dispatch],
  );

  // Use the auto-resize hook with height change callback
  const {
    smartResize,
    handleGripMouseDown,
    handleGripTouchStart,
    increaseHeightForEmptyContent,
  } = useAutoResize(chatInputRef as React.RefObject<HTMLElement | null>, {
    minHeight: 20,
    maxHeight: 400,
    onHeightChange: handleHeightChange,
    onGripDragStart: handleDragStart,
    onGripDragEnd: handleDragEnd,
    value: messageToSend ?? undefined,
    enableManualResize: true,
  });

  return {
    gripRef,
    isGripVisible,
    handleTopEdgeClick,
    smartResize,
    handleGripMouseDown,
    handleGripTouchStart,
    increaseHeightForEmptyContent,
  };
};
