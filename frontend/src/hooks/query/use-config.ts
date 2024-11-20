import { useQuery } from "@tanstack/react-query";
import React from "react";
import { GetConfigResponse } from "#/api/open-hands.types";

const getConfigQueryFn = async (): Promise<GetConfigResponse> => {
  const response = await fetch("/config.json");
  return response.json();
};

export const useConfig = () => {
  const config = useQuery({
    queryKey: ["config"],
    queryFn: getConfigQueryFn,
  });

  // Remove this. Instead, we should retrieve the data directly from the config query
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
