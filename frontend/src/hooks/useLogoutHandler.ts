import React from "react";
import { useConfig } from "#/hooks/query/use-config";
import { createLogoutHandler } from "#/utils/auth-utils";

export const useLogoutHandler = () => {
  const { data: config } = useConfig();
  const appMode = React.useMemo(() => config?.APP_MODE, [config]);

  return React.useMemo(() => createLogoutHandler(appMode), [appMode]);
};
