import { useCallback, useRef } from "react";
import notificationSound from "../assets/notification.mp3";
import { useCurrentSettings } from "../context/settings-context";

export const useNotification = () => {
  const { settings } = useCurrentSettings();
  const audioRef = useRef<HTMLAudioElement | undefined>(undefined);

  // Initialize audio only in browser environment
  if (typeof window !== "undefined" && !audioRef.current) {
    audioRef.current = new Audio(notificationSound);
    audioRef.current.volume = 0.5;
  }

  const notify = useCallback(async (title: string, options?: NotificationOptions) => {
    if (typeof window === "undefined") return;

    if (settings?.ENABLE_SOUND_NOTIFICATIONS && audioRef.current) {
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
      return new Notification(title, options);
    }
  }, [settings?.ENABLE_SOUND_NOTIFICATIONS]);

  return { notify };
};
