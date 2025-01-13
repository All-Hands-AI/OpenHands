export const sendNotification = (title: string, options?: NotificationOptions) => {
  if (!('Notification' in window)) {
    console.warn('This browser does not support desktop notifications');
    return;
  }

  const notificationsEnabled = localStorage.getItem('notifications-enabled') === 'true';
  if (!notificationsEnabled) {
    return;
  }

  if (Notification.permission === 'granted') {
    new Notification(title, options);
  }
};
