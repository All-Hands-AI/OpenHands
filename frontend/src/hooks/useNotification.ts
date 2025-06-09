import { useCallback, useRef } from "react";
import notificationSound from "../assets/notification.mp3";
import { useSettings } from "./query/use-settings";

export const useNotification = () => {
  const { data: settings } = useSettings();
  const audioRef = useRef<HTMLAudioElement | undefined>(undefined);

  // Initialize audio only in browser environment
  if (typeof window !== "undefined" && !audioRef.current) {
    audioRef.current = new Audio(notificationSound);
    audioRef.current.volume = 0.5;
  }

  const notify = useCallback(
    async (
      title: string,
      options?: NotificationOptions & { playSound?: boolean },
    ): Promise<Notification | undefined> => {
      if (typeof window === "undefined") return undefined;

      // Only play sound if:
      // 1. Explicitly requested via playSound option
      // 2. Sound notifications are enabled in settings
      // 3. Audio is available
      // 4. Not a settings-related notification
      if (
        options?.playSound === true && // Must be explicitly true
        settings?.ENABLE_SOUND_NOTIFICATIONS &&
        audioRef.current &&
        !title.includes("BUTTON$") // Don't play for button/settings actions
      ) {
        // Reset and play sound
        audioRef.current.currentTime = 0;
        audioRef.current.play().catch(() => {
          // Ignore autoplay errors
        });
      }

      if (Notification.permission === "default") {
        await Notification.requestPermission();
      }

      if (Notification.permission === "granted") {
        // Remove playSound from options before passing to Notification
        const { playSound, ...notificationOptions } = options || {};
        return new Notification(title, notificationOptions);
      }

      return undefined;
    },
    [settings?.ENABLE_SOUND_NOTIFICATIONS],
  );

  return { notify };
};
