import { useEffect } from "react";
import { useConfig } from "./query/use-config";
import { appModeStore } from "#/utils/app-mode-store";

/**
 * Hook to sync the APP_MODE from the config to the app mode store
 * This ensures the axios interceptor always has access to the current APP_MODE
 */
export const useAppModeSync = () => {
  const { data: config } = useConfig();

  useEffect(() => {
    if (config?.APP_MODE) {
      appModeStore.setAppMode(config.APP_MODE);
    }
  }, [config?.APP_MODE]);
};
