import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { NotificationSettings } from '../../src/components/features/notifications/notification-settings';

describe('NotificationSettings', () => {
  beforeEach(() => {
    // Mock localStorage
    Storage.prototype.getItem = vi.fn();
    Storage.prototype.setItem = vi.fn();

    // Mock Notification API
    Object.defineProperty(window, 'Notification', {
      value: {
        requestPermission: vi.fn(),
        permission: 'default',
      },
      writable: true,
    });
  });

  it('renders notification settings', () => {
    render(<NotificationSettings />);
    expect(screen.getByText('Browser Notifications')).toBeInTheDocument();
    expect(screen.getByText('Get notified when the agent completes its task')).toBeInTheDocument();
    expect(screen.getByRole('checkbox')).toBeInTheDocument();
  });

  it('requests notification permission when enabling notifications', async () => {
    (window.Notification.requestPermission as ReturnType<typeof vi.fn>).mockResolvedValue('granted');

    render(<NotificationSettings />);
    const checkbox = screen.getByRole('checkbox');

    fireEvent.click(checkbox);

    await waitFor(() => {
      expect(window.Notification.requestPermission).toHaveBeenCalled();
      expect(localStorage.setItem).toHaveBeenCalledWith('notifications-enabled', 'true');
    });
  });

  it('disables notifications when toggling off', async () => {
    render(<NotificationSettings />);
    const checkbox = screen.getByRole('checkbox');

    // First enable notifications
    (window.Notification.requestPermission as ReturnType<typeof vi.fn>).mockResolvedValue('granted');
    fireEvent.click(checkbox);
    await waitFor(() => {
      expect(localStorage.setItem).toHaveBeenCalledWith('notifications-enabled', 'true');
    });

    // Then disable them
    fireEvent.click(checkbox);
    expect(localStorage.setItem).toHaveBeenCalledWith('notifications-enabled', 'false');
  });

  it('does not enable notifications if permission is denied', async () => {
    (window.Notification.requestPermission as ReturnType<typeof vi.fn>).mockResolvedValue('denied');

    render(<NotificationSettings />);
    const checkbox = screen.getByRole('checkbox');

    fireEvent.click(checkbox);

    await waitFor(() => {
      expect(window.Notification.requestPermission).toHaveBeenCalled();
      expect(localStorage.setItem).not.toHaveBeenCalledWith('notifications-enabled', 'true');
    });
  });
});
