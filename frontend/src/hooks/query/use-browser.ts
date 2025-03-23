import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getQueryReduxBridge } from "#/utils/query-redux-bridge";

interface BrowserState {
  url: string;
  screenshotSrc: string;
}

// Initial state
const initialBrowser: BrowserState = {
  url: "https://github.com/All-Hands-AI/OpenHands",
  screenshotSrc: "",
};

/**
 * Hook to access and manipulate browser data using React Query
 * This replaces the Redux browser slice functionality
 */
export function useBrowser() {
  const queryClient = useQueryClient();

  // Try to get the bridge, but don't throw if it's not initialized (for tests)
  let bridge: ReturnType<typeof getQueryReduxBridge> | null = null;
  try {
    bridge = getQueryReduxBridge();
  } catch (error) {
    // In tests, we might not have the bridge initialized
    // eslint-disable-next-line no-console
    console.warn(
      "QueryReduxBridge not initialized, using default browser state",
    );
  }

  // Get initial state from Redux if this is the first time accessing the data
  const getInitialBrowserState = (): BrowserState => {
    // If we already have data in React Query, use that
    const existingData = queryClient.getQueryData<BrowserState>(["browser"]);
    if (existingData) return existingData;

    // Otherwise, get initial data from Redux if bridge is available
    if (bridge) {
      try {
        return bridge.getReduxSliceState<BrowserState>("browser");
      } catch (error) {
        // If we can't get the state from Redux, return the initial state
        return initialBrowser;
      }
    }

    // If bridge is not available, return the initial state
    return initialBrowser;
  };

  // Query for browser state
  const query = useQuery({
    queryKey: ["browser"],
    queryFn: () => {
      // First check if we already have data in the query cache
      const existingData = queryClient.getQueryData<BrowserState>(["browser"]);
      if (existingData) return existingData;

      // Otherwise get from the bridge or use initial state
      return getInitialBrowserState();
    },
    initialData: initialBrowser, // Use initialBrowser directly to ensure it's always defined
    staleTime: Infinity, // We manage updates manually through mutations
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });

  // Function to directly set the URL (synchronous)
  const setUrlSync = (url: string) => {
    // Get current state
    const previousState =
      queryClient.getQueryData<BrowserState>(["browser"]) || initialBrowser;

    // Update state
    const newState = {
      ...previousState,
      url,
    };

    // Set the state synchronously
    queryClient.setQueryData<BrowserState>(["browser"], newState);
  };

  // We don't need the mutation since we're using the sync function directly

  // Function to directly set the screenshot source (synchronous)
  const setScreenshotSrcSync = (screenshotSrc: string) => {
    // Get current state
    const previousState =
      queryClient.getQueryData<BrowserState>(["browser"]) || initialBrowser;

    // Update state
    const newState = {
      ...previousState,
      screenshotSrc,
    };

    // Set the state synchronously
    queryClient.setQueryData<BrowserState>(["browser"], newState);
  };

  // We don't need the mutation since we're using the sync function directly

  return {
    // State
    url: query.data?.url || initialBrowser.url,
    screenshotSrc: query.data?.screenshotSrc || initialBrowser.screenshotSrc,
    isLoading: query.isLoading,

    // Actions
    setUrl: setUrlSync,
    setScreenshotSrc: setScreenshotSrcSync,
  };
}
