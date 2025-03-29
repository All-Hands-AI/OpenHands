import { useQuery, useQueryClient } from "@tanstack/react-query";

interface BrowserState {
  url: string;
  screenshotSrc: string;
}

const initialBrowser: BrowserState = {
  url: "https://github.com/All-Hands-AI/OpenHands",
  screenshotSrc: "",
};

export function useBrowser() {
  const queryClient = useQueryClient();

  const getInitialBrowserState = (): BrowserState => {
    const existingData = queryClient.getQueryData<BrowserState>(["browser"]);
    if (existingData) return existingData;
    return initialBrowser;
  };

  const query = useQuery({
    queryKey: ["browser"],
    queryFn: () => {
      const existingData = queryClient.getQueryData<BrowserState>(["browser"]);
      if (existingData) return existingData;
      return getInitialBrowserState();
    },
    initialData: initialBrowser,
    staleTime: Infinity,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  const setUrlSync = (url: string) => {
    const previousState =
      queryClient.getQueryData<BrowserState>(["browser"]) || initialBrowser;

    const newState = {
      ...previousState,
      url,
    };

    queryClient.setQueryData<BrowserState>(["browser"], newState);
  };

  const setScreenshotSrcSync = (screenshotSrc: string) => {
    const previousState =
      queryClient.getQueryData<BrowserState>(["browser"]) || initialBrowser;

    const newState = {
      ...previousState,
      screenshotSrc,
    };

    queryClient.setQueryData<BrowserState>(["browser"], newState);
  };

  return {
    url: query.data?.url || initialBrowser.url,
    screenshotSrc: query.data?.screenshotSrc || initialBrowser.screenshotSrc,
    isLoading: query.isLoading,
    setUrl: setUrlSync,
    setScreenshotSrc: setScreenshotSrcSync,
  };
}
