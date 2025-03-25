import { useQueryClient } from "@tanstack/react-query";
import React from "react";

const BROWSER_KEY = ["_STATE", "browser"];

interface BrowserData {
  url: string;
  screenshotSrc: string;
}

export const DEFAULT_BROWSER_DATA: BrowserData = {
  url: "https://github.com/All-Hands-AI/OpenHands",
  screenshotSrc: "",
};

export const useBrowser = () => {
  const queryClient = useQueryClient();

  const setUrl = React.useCallback(
    (url: string) => {
      queryClient.setQueryData<BrowserData>(BROWSER_KEY, (old) => ({
        ...(old || DEFAULT_BROWSER_DATA),
        url,
      }));
    },
    [queryClient],
  );

  const setScreenshotSrc = React.useCallback(
    (screenshotSrc: string) => {
      queryClient.setQueryData<BrowserData>(BROWSER_KEY, (old) => ({
        ...(old || DEFAULT_BROWSER_DATA),
        screenshotSrc,
      }));
    },
    [queryClient],
  );

  const { url, screenshotSrc } =
    queryClient.getQueryData<BrowserData>(BROWSER_KEY) || DEFAULT_BROWSER_DATA;

  return {
    url,
    screenshotSrc,
    setUrl,
    setScreenshotSrc,
  };
};
