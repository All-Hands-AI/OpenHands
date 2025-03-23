import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useMemo,
} from "react";

// Context type definition
type BrowserContextType = {
  url: string;
  screenshotSrc: string;
  setUrl: (url: string) => void;
  setScreenshotSrc: (src: string) => void;
};

// Create context with default values
const BrowserContext = createContext<BrowserContextType>({
  url: "https://github.com/All-Hands-AI/OpenHands",
  screenshotSrc: "",
  setUrl: () => {},
  setScreenshotSrc: () => {},
});

// Provider component
export function BrowserProvider({ children }: { children: React.ReactNode }) {
  const [url, setUrlState] = useState<string>(
    "https://github.com/All-Hands-AI/OpenHands",
  );
  const [screenshotSrc, setScreenshotSrcState] = useState<string>("");

  const setUrl = useCallback((newUrl: string) => {
    setUrlState(newUrl);
  }, []);

  const setScreenshotSrc = useCallback((src: string) => {
    setScreenshotSrcState(src);
  }, []);

  // Register the functions with the browser service
  React.useEffect(() => {
    import("#/services/context-services/browser-service").then(
      ({ registerBrowserFunctions }) => {
        registerBrowserFunctions({
          setUrl,
          setScreenshotSrc,
          getUrl: () => url,
          getScreenshotSrc: () => screenshotSrc,
        });
      },
    );
  }, [setUrl, setScreenshotSrc, url, screenshotSrc]);

  // Create a memoized context value to prevent unnecessary re-renders
  const contextValue = useMemo(
    () => ({
      url,
      screenshotSrc,
      setUrl,
      setScreenshotSrc,
    }),
    [url, screenshotSrc, setUrl, setScreenshotSrc],
  );

  return (
    <BrowserContext.Provider value={contextValue}>
      {children}
    </BrowserContext.Provider>
  );
}

// Custom hook to use the browser context
export function useBrowserContext() {
  const context = useContext(BrowserContext);

  if (context === undefined) {
    throw new Error("useBrowserContext must be used within a BrowserProvider");
  }

  return context;
}
