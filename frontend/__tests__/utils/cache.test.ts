import { afterEach } from "node:test";
import { beforeEach, describe, expect, it, vi } from "vitest";

const cache = {
  set: (key: string, data: any, ttl: number) => {
    const expiration = Date.now() + ttl;
    const entry = { data, expiration };
    localStorage.setItem(`app_cache_${key}`, JSON.stringify(entry));
  },
  get: (key: string) => {
    const entry = JSON.parse(localStorage.getItem(`app_cache_${key}`) || "");
    if (entry.expiration < Date.now()) {
      cache.delete(key);
      return null;
    }
    return entry.data;
  },
  delete: (key: string) => {
    localStorage.removeItem(`app_cache_${key}`);
  },
  clearAll: () => {
    const keysToRemove = Object.keys(localStorage).filter((key) =>
      key.startsWith("app_cache_"),
    );
    keysToRemove.forEach((key) => {
      localStorage.removeItem(key);
    });
  },
};

describe("Cache", () => {
  const testKey = "key";
  const testData = { message: "Hello, world!" };
  const testTTL = 1000; // 1 second

  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("sets data in localStorage with expiration", () => {
    cache.set(testKey, testData, testTTL);
    const cachedEntry = JSON.parse(
      localStorage.getItem(`app_cache_${testKey}`) || "",
    );

    expect(cachedEntry.data).toEqual(testData);
    expect(cachedEntry.expiration).toBeGreaterThan(Date.now());
  });

  it("gets data from localStorage if not expired", () => {
    cache.set(testKey, testData, testTTL);

    expect(cache.get(testKey)).toEqual(testData);
  });

  it("returns null if cached data is expired", () => {
    cache.set(testKey, testData, testTTL);

    vi.advanceTimersByTime(testTTL + 1);
    expect(cache.get(testKey)).toBeNull();
    expect(localStorage.getItem(`app_cache_${testKey}`)).toBeNull();
  });

  it("deletes data from localStorage", () => {
    cache.set(testKey, testData, testTTL);
    cache.delete(testKey);

    expect(localStorage.getItem(`app_cache_${testKey}`)).toBeNull();
  });

  it("clears all data with the app prefix from localStorage", () => {
    cache.set(testKey, testData, testTTL);
    cache.set("anotherKey", { data: "More data" }, testTTL);
    cache.clearAll();

    expect(localStorage.length).toBe(0);
  });

  it("does not retrieve non-prefixed data from localStorage when clearing", () => {
    localStorage.setItem("nonPrefixedKey", "should remain");
    cache.set(testKey, testData, testTTL);
    cache.clearAll();
    expect(localStorage.getItem("nonPrefixedKey")).toBe("should remain");
  });
});
