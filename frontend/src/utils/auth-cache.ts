import type { GitHubUser, GitHubErrorReponse } from "#/types/github";

interface CacheEntry<T> {
  value: T;
  timestamp: number;
  token: string;
}

type GitHubUserResponse = GitHubUser | GitHubErrorReponse;

class AuthCache {
  private static instance: AuthCache;
  private cache: {
    isAuthed?: CacheEntry<boolean>;
    githubUser?: CacheEntry<GitHubUserResponse>;
  } = {};

  private constructor() {}

  static getInstance(): AuthCache {
    if (!AuthCache.instance) {
      AuthCache.instance = new AuthCache();
    }
    return AuthCache.instance;
  }

  private isExpired<T>(entry: CacheEntry<T>, maxAge: number): boolean {
    return Date.now() - entry.timestamp > maxAge;
  }

  private tokenChanged<T>(entry: CacheEntry<T>, currentToken: string): boolean {
    return entry.token !== currentToken;
  }

  getAuthStatus(token: string): boolean | undefined {
    const entry = this.cache.isAuthed;
    if (!entry || this.isExpired(entry, 60000) || this.tokenChanged(entry, token)) {
      return undefined;
    }
    return entry.value;
  }

  setAuthStatus(token: string, value: boolean): void {
    this.cache.isAuthed = {
      value,
      timestamp: Date.now(),
      token,
    };
  }

  getGithubUser(token: string): GitHubUserResponse | undefined {
    const entry = this.cache.githubUser;
    if (!entry || this.isExpired(entry, 300000) || this.tokenChanged(entry, token)) {
      return undefined;
    }
    return entry.value;
  }

  setGithubUser(token: string, value: GitHubUserResponse): void {
    this.cache.githubUser = {
      value,
      timestamp: Date.now(),
      token,
    };
  }

  clear(): void {
    this.cache = {};
  }
}

export const authCache = AuthCache.getInstance();