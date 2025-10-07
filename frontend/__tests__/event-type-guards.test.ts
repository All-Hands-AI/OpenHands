import { describe, it, expect } from 'vitest';
import { isV1Event, isV0Event } from '../src/types/v1/type-guards';

describe('Event Type Guards - Core Functionality', () => {
  describe('isV1Event', () => {
    it('should return true for objects with string IDs', () => {
      const mockV1Event = {
        id: '01HZXYZ123ABC456DEF789GHI',
        timestamp: '2024-01-01T00:00:00Z',
        source: 'agent'
      };

      expect(isV1Event(mockV1Event as any)).toBe(true);
    });

    it('should return false for objects with numeric IDs', () => {
      const mockV0Event = {
        id: 123,
        source: 'agent',
        message: 'test message',
        timestamp: '2024-01-01T00:00:00Z',
        action: 'run'
      };

      expect(isV1Event(mockV0Event as any)).toBe(false);
    });
  });

  describe('isV0Event', () => {
    it('should return true for objects with numeric IDs and action property', () => {
      const mockV0Event = {
        id: 123,
        source: 'agent',
        message: 'test message',
        timestamp: '2024-01-01T00:00:00Z',
        action: 'run'
      };

      expect(isV0Event(mockV0Event as any)).toBe(true);
    });

    it('should return true for objects with numeric IDs and observation property', () => {
      const mockV0Event = {
        id: 123,
        source: 'agent',
        message: 'test message',
        timestamp: '2024-01-01T00:00:00Z',
        observation: 'run'
      };

      expect(isV0Event(mockV0Event as any)).toBe(true);
    });

    it('should return false for objects with string IDs', () => {
      const mockV1Event = {
        id: '01HZXYZ123ABC456DEF789GHI',
        timestamp: '2024-01-01T00:00:00Z',
        source: 'agent'
      };

      expect(isV0Event(mockV1Event as any)).toBe(false);
    });

    it('should return false for objects with numeric IDs but no action/observation', () => {
      const mockEvent = {
        id: 123,
        source: 'agent',
        message: 'test message',
        timestamp: '2024-01-01T00:00:00Z'
      };

      expect(isV0Event(mockEvent as any)).toBe(false);
    });
  });

  describe('Edge cases', () => {
    it('should handle null/undefined gracefully', () => {
      expect(isV1Event(null as any)).toBe(false);
      expect(isV0Event(null as any)).toBe(false);
      expect(isV1Event(undefined as any)).toBe(false);
      expect(isV0Event(undefined as any)).toBe(false);
    });

    it('should handle objects without id property', () => {
      const invalidEvent = { source: 'agent', timestamp: '2024-01-01T00:00:00Z' };
      expect(isV1Event(invalidEvent as any)).toBe(false);
      expect(isV0Event(invalidEvent as any)).toBe(false);
    });

    it('should handle non-object values', () => {
      expect(isV1Event('string' as any)).toBe(false);
      expect(isV0Event(123 as any)).toBe(false);
      expect(isV1Event(true as any)).toBe(false);
      expect(isV0Event([] as any)).toBe(false);
    });
  });

  describe('Type narrowing', () => {
    it('should correctly identify V1 vs V0 events', () => {
      const v1Event = {
        id: '01HZXYZ123ABC456DEF789GHI',
        timestamp: '2024-01-01T00:00:00Z',
        source: 'agent'
      };

      const v0Event = {
        id: 456,
        source: 'agent',
        message: 'test message',
        timestamp: '2024-01-01T00:00:00Z',
        action: 'run'
      };

      // Test mutual exclusivity
      expect(isV1Event(v1Event as any)).toBe(true);
      expect(isV0Event(v1Event as any)).toBe(false);

      expect(isV0Event(v0Event as any)).toBe(true);
      expect(isV1Event(v0Event as any)).toBe(false);
    });
  });
});