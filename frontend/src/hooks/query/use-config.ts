import { useQuery } from "@tanstack/react-query";
import React from "react";
import OpenHands from "#/api/open-hands";

export const useConfig = () => {
  const config = useQuery({
    queryKey: ["config"],
    queryFn: OpenHands.getConfig,
  });

  React.useEffect(() => {
    if (config.data) {
      window.__APP_MODE__ = config.data.APP_MODE;
      window.__GITHUB_CLIENT_ID__ = config.data.GITHUB_CLIENT_ID;
    } else if (config.isError) {
      window.__APP_MODE__ = "oss";
      window.__GITHUB_CLIENT_ID__ = null;
    }
  }, [config.data, config.isError]);

  return config;
};
