import useSound from "use-sound";
import notificationSound from "../assets/notification.mp3";

export const useNotification = () => {
  const [playSound] = useSound(notificationSound);

  const notify = (
    title: string,
    options?: NotificationOptions,
  ): Notification | void => {
    // Play sound
    playSound();

    // Request permission for browser notifications if not granted
    if (Notification.permission !== "granted") {
      Notification.requestPermission();
    }

    // Show browser notification if permission is granted
    if (Notification.permission === "granted") {
      const notification = new Notification(title, options);
      return notification;
    }

    // Change favicon to indicate notification (add dot)
    const favicon = document.querySelector(
      'link[rel="icon"]',
    ) as HTMLLinkElement;
    if (favicon) {
      const canvas = document.createElement("canvas");
      canvas.width = 32;
      canvas.height = 32;
      const ctx = canvas.getContext("2d");
      if (ctx) {
        // Draw original favicon
        const img = new Image();
        img.src = favicon.href;
        img.onload = () => {
          ctx.drawImage(img, 0, 0, 32, 32);
          // Draw notification dot
          ctx.beginPath();
          ctx.arc(24, 8, 8, 0, 2 * Math.PI);
          ctx.fillStyle = "#ff0000";
          ctx.fill();
          favicon.href = canvas.toDataURL("image/png");
        };
      }
    }
    return undefined;
  };

  return { notify };
};
