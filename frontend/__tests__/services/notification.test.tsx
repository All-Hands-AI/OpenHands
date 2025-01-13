import { describe, it, expect, beforeEach, vi } from 'vitest';
import { sendNotification } from '../../src/services/notification';

type MockNotification = {
  (title: string, options?: NotificationOptions): void;
  permission: NotificationPermission;
};

describe('sendNotification', () => {
  beforeEach(() => {
    // Mock localStorage
    Storage.prototype.getItem = vi.fn() as jest.Mock;
    Storage.prototype.setItem = vi.fn() as jest.Mock;

    // Mock Notification API
    const mockNotification = vi.fn((title, options) => ({
      title,
      ...options,
    })) as unknown as MockNotification;
    mockNotification.permission = 'granted';
    Object.defineProperty(window, 'Notification', {
      value: mockNotification,
      writable: true,
    });
  });

  it('should send notification when notifications are enabled', () => {
    // Mock notifications being enabled
    Storage.prototype.getItem.mockReturnValue('true');

    const title = 'Test Title';
    const options = {
      body: 'Test Body',
      icon: '/test-icon.png'
    };

    sendNotification(title, options);

    expect(window.Notification).toHaveBeenCalledWith(title, options);
  });

  it('should not send notification when notifications are disabled', () => {
    // Mock notifications being disabled
    Storage.prototype.getItem.mockReturnValue('false');

    sendNotification('Test Title', { body: 'Test Body' });

    expect(window.Notification).not.toHaveBeenCalled();
  });

  it('should not send notification when permission is not granted', () => {
    // Mock notifications being enabled but permission not granted
    Storage.prototype.getItem.mockReturnValue('true');
    const mockNotification = vi.fn((title, options) => ({
      title,
      ...options,
    }));
    mockNotification.permission = 'denied';
    Object.defineProperty(window, 'Notification', {
      value: mockNotification,
      writable: true,
    });

    sendNotification('Test Title', { body: 'Test Body' });

    expect(mockNotification).not.toHaveBeenCalled();
  });
});