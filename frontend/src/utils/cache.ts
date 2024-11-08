type CacheKey = string;
type CacheEntry<T> = {
  data: T;
  expiration: number;
};

class Cache {
  private prefix = "app_cache_";

  private defaultTTL = 5 * 60 * 1000; // 5 minutes

  /**
   * Generate a unique key with prefix for local storage
   * @param key The key to be stored in local storage
   * @returns The unique key with prefix
   */
  private getKey(key: CacheKey): string {
    return `${this.prefix}${key}`;
  }

  /**
   * Retrieve the cached data from local storage
   * @param key The key to be retrieved from local storage
   * @returns The data stored in local storage
   */
  public get<T>(key: CacheKey): T | null {
    const cachedEntry = localStorage.getItem(this.getKey(key));
    if (cachedEntry) {
      const { data, expiration } = JSON.parse(cachedEntry) as CacheEntry<T>;
      if (Date.now() < expiration) return data;
      this.delete(key); // Remove expired cache
    }

    return null;
  }

  /**
   * Store the data in local storage with expiration
   * @param key The key to be stored in local storage
   * @param data The data to be stored in local storage
   * @param ttl The time to live for the data in milliseconds
   * @returns void
   */
  public set<T>(key: CacheKey, data: T, ttl = this.defaultTTL): void {
    const expiration = Date.now() + ttl;
    const entry: CacheEntry<T> = { data, expiration };
    localStorage.setItem(this.getKey(key), JSON.stringify(entry));
  }

  /**
   * Remove the data from local storage
   * @param key The key to be removed from local storage
   * @returns void
   */
  public delete(key: CacheKey): void {
    localStorage.removeItem(this.getKey(key));
  }

  /**
   * Clear all data with the app prefix from local storage
   * @returns void
   */
  public clearAll(): void {
    Object.keys(localStorage).forEach((key) => {
      if (key.startsWith(this.prefix)) localStorage.removeItem(key);
    });
  }
}

export const cache = new Cache();
