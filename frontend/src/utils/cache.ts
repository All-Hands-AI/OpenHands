type CacheKey = string;
type CacheEntry<T> = {
  data: T;
  expiration: number;
};

class Cache {
  private defaultTTL = 5 * 60 * 1000; // 5 minutes

  private cacheMemory: Record<string, string> = {};

  /**
   * Retrieve the cached data from memory
   * @param key The key to be retrieved from memory
   * @returns The data stored in memory
   */
  public get<T>(key: CacheKey): T | null {
    const cachedEntry = this.cacheMemory[key];
    if (cachedEntry) {
      const { data, expiration } = JSON.parse(cachedEntry) as CacheEntry<T>;
      if (Date.now() < expiration) return data;
      this.delete(key); // Remove expired cache
    }

    return null;
  }

  /**
   * Store the data in memory with expiration
   * @param key The key to be stored in memory
   * @param data The data to be stored in memory
   * @param ttl The time to live for the data in milliseconds
   * @returns void
   */
  public set<T>(key: CacheKey, data: T, ttl = this.defaultTTL): void {
    const expiration = Date.now() + ttl;
    const entry: CacheEntry<T> = { data, expiration };
    this.cacheMemory[key] = JSON.stringify(entry);
  }

  /**
   * Remove the data from memory
   * @param key The key to be removed from memory
   * @returns void
   */
  public delete(key: CacheKey): void {
    delete this.cacheMemory[key];
  }

  /**
   * Clear all data
   * @returns void
   */
  public clearAll(): void {
    Object.keys(this.cacheMemory).forEach((key) => {
      delete this.cacheMemory[key];
    });
  }
}

export const cache = new Cache();
