import { afterEach } from "node:test";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { cache } from "#/utils/cache";

describe("Cache", () => {
  const testKey = "key";
  const testData = { message: "Hello, world!" };
  const testTTL = 1000; // 1 second

  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("sets data in memory with expiration", () => {
    cache.set(testKey, testData, testTTL);
    const cachedEntry = JSON.parse(
      cached.cacheMemory[`app_cache_${testKey}`] || "",
    );

    expect(cachedEntry.data).toEqual(testData);
    expect(cachedEntry.expiration).toBeGreaterThan(Date.now());
  });

  it("gets data from memory if not expired", () => {
    cache.set(testKey, testData, testTTL);

    expect(cache.get(testKey)).toEqual(testData);
  });

  it("should expire after 5 minutes by default", () => {
    cache.set(testKey, testData);
    expect(cache.get(testKey)).not.toBeNull();

    vi.advanceTimersByTime(5 * 60 * 1000 + 1);

    expect(cache.get(testKey)).toBeNull();
    expect(cache.cacheMemory[`app_cache_${testKey}`]).toBeNull();
  });

  it("returns null if cached data is expired", () => {
    cache.set(testKey, testData, testTTL);

    vi.advanceTimersByTime(testTTL + 1);
    expect(cache.get(testKey)).toBeNull();
    expect(cache.cacheMemory[`app_cache_${testKey}`]).toBeNull();
  });

  it("deletes data from memory", () => {
    cache.set(testKey, testData, testTTL);
    cache.delete(testKey);

    expect(cache.cacheMemory[`app_cache_${testKey}`]).toBeNull();
  });

  it("clears all data with the app prefix from memory", () => {
    cache.set(testKey, testData, testTTL);
    cache.set("anotherKey", { data: "More data" }, testTTL);
    cache.clearAll();

    expect(Object.keys(cache.cacheMemory)).toBe(0);
  });
});
