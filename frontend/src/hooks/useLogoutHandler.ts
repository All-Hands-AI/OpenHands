import React from "react";
import { createLogoutHandler } from "#/utils/auth-utils";

export const useLogoutHandler = (appMode?: string) =>
  React.useMemo(() => createLogoutHandler(appMode), [appMode]);
