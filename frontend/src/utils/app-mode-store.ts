/**
 * A simple store to keep track of the current APP_MODE
 * This is used by the axios interceptor to modify API paths
 */

type AppMode = "saas" | "oss" | null;

class AppModeStore {
  private static instance: AppModeStore;
  private _appMode: AppMode = null;

  private constructor() {}

  public static getInstance(): AppModeStore {
    if (!AppModeStore.instance) {
      AppModeStore.instance = new AppModeStore();
    }
    return AppModeStore.instance;
  }

  public getAppMode(): AppMode {
    return this._appMode;
  }

  public setAppMode(appMode: AppMode): void {
    this._appMode = appMode;
  }
}

export const appModeStore = AppModeStore.getInstance();
