import React from 'react';
import { useLocalStorage } from '#/hooks/use-local-storage';

export const NotificationSettings: React.FC = () => {
  const [notificationsEnabled, setNotificationsEnabled] = useLocalStorage('notifications-enabled', false);

  const handleToggleNotifications = async () => {
    if (!notificationsEnabled) {
      try {
        const permission = await Notification.requestPermission();
        if (permission === 'granted') {
          setNotificationsEnabled(true);
        }
      } catch (error) {
        console.error('Error requesting notification permission:', error);
      }
    } else {
      setNotificationsEnabled(false);
    }
  };

  return (
    <div className="flex items-center justify-between p-4 border-b">
      <div>
        <h3 className="text-lg font-medium">Browser Notifications</h3>
        <p className="text-sm text-gray-500">Get notified when the agent completes its task</p>
      </div>
      <label className="relative inline-flex items-center cursor-pointer">
        <input
          type="checkbox"
          className="sr-only peer"
          checked={notificationsEnabled}
          onChange={handleToggleNotifications}
        />
        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
      </label>
    </div>
  );
};
