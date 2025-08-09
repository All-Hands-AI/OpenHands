import { useEffect } from "react";

interface UseKeyboardShortcutProps {
  key: string;
  ctrlKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  callback: () => void;
  enabled?: boolean;
}

export function useKeyboardShortcut({
  key,
  ctrlKey = false,
  shiftKey = false,
  altKey = false,
  callback,
  enabled = true,
}: UseKeyboardShortcutProps) {
  useEffect(() => {
    if (!enabled) return;

    const handleKeyPress = (event: KeyboardEvent) => {
      if (
        event.key.toLowerCase() === key.toLowerCase() &&
        event.ctrlKey === ctrlKey &&
        event.shiftKey === shiftKey &&
        event.altKey === altKey
      ) {
        event.preventDefault();
        callback();
      }
    };

    window.addEventListener("keydown", handleKeyPress);
    // eslint-disable-next-line consistent-return
    return () => {
      window.removeEventListener("keydown", handleKeyPress);
    };
  }, [key, ctrlKey, shiftKey, altKey, callback, enabled]);
}
