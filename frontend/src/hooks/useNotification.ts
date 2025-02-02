import useSound from "use-sound";
import notificationSound from "../assets/notification.mp3";
import { useCurrentSettings } from "../context/settings-context";

export const useNotification = () => {
  const [playSound] = useSound(notificationSound);
  const { settings } = useCurrentSettings();

  const notify = async (title: string, options?: NotificationOptions) => {
    if (settings?.ENABLE_SOUND_NOTIFICATIONS) {
      playSound();
    }

    if (Notification.permission === "default") {
      await Notification.requestPermission();
    }

    if (Notification.permission === "granted") {
      return new Notification(title, options);
    }
  };

  return { notify };
};
