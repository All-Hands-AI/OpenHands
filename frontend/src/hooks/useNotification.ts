import { Howl } from "howler";
import { useCallback } from "react";
import notificationSound from "../assets/notification.mp3";
import { useCurrentSettings } from "../context/settings-context";

// Create sound instance outside the hook to avoid recreation
const sound = new Howl({
  src: [notificationSound],
  volume: 0.5,
});

export const useNotification = () => {
  const { settings } = useCurrentSettings();

  const notify = useCallback(async (title: string, options?: NotificationOptions) => {
    if (settings?.ENABLE_SOUND_NOTIFICATIONS) {
      sound.play();
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
