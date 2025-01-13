import { vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

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
