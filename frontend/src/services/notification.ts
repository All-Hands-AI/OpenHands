export const sendNotification = async (
  title: string,
  options?: NotificationOptions,
) => {
  if (!("Notification" in window)) {
    // eslint-disable-next-line no-console
    console.warn("This browser does not support desktop notifications");
    return;
  }

  const notificationsEnabled =
    localStorage.getItem("notifications-enabled") === "true";
  if (!notificationsEnabled) {
    return;
  }

  if (Notification.permission === "granted") {
    // eslint-disable-next-line no-new
    new Notification(title, options);
  } else if (Notification.permission !== "denied") {
    const permission = await Notification.requestPermission();
    if (permission === "granted") {
      // eslint-disable-next-line no-new
      new Notification(title, options);
    }
  }
};
