import { useCallback } from "react";
import notificationSound from "../assets/notification.mp3";
import { useCurrentSettings } from "../context/settings-context";

// Create audio element outside the hook to avoid recreation
const audio = new Audio(notificationSound);
audio.volume = 0.5;

export const useNotification = () => {
  const { settings } = useCurrentSettings();

  const notify = useCallback(async (title: string, options?: NotificationOptions) => {
    if (settings?.ENABLE_SOUND_NOTIFICATIONS) {
      // Reset and play sound
      audio.currentTime = 0;
      audio.play().catch(() => {
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
