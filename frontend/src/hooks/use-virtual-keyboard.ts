import { useEffect, useRef } from "react";
import { getVirtualKeyboardManager } from "#/utils/utils";

/**
 * Hook for managing virtual keyboard state and cleanup
 * Provides access to the virtual keyboard manager with proper lifecycle management
 */
export const useVirtualKeyboard = () => {
  const managerRef = useRef<ReturnType<
    typeof getVirtualKeyboardManager
  > | null>(null);

  useEffect(() => {
    // Get the global virtual keyboard manager
    managerRef.current = getVirtualKeyboardManager();

    // Cleanup function
    return () => {
      // Note: We don't destroy the global manager here as it's shared across the app
      // The global manager will be cleaned up when the app unmounts
      managerRef.current = null;
    };
  }, []);

  return {
    /**
     * Check if the virtual keyboard is currently visible
     */
    isKeyboardVisible: () => managerRef.current?.isKeyboardVisible() ?? false,

    /**
     * Add a listener for keyboard visibility changes
     * Returns a cleanup function to remove the listener
     */
    addListener: (callback: () => void) =>
      managerRef.current?.addListener(callback) ?? (() => {}),
  };
};
