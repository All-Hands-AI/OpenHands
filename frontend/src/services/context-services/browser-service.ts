// Function types
type SetUrlFn = (url: string) => void;
type SetScreenshotSrcFn = (src: string) => void;
type GetUrlFn = () => string;
type GetScreenshotSrcFn = () => string;

// Module-level variables to store the actual functions
let setUrlImpl: SetUrlFn = () => {};
let setScreenshotSrcImpl: SetScreenshotSrcFn = () => {};
let getUrlImpl: GetUrlFn = () => "https://github.com/All-Hands-AI/OpenHands";
let getScreenshotSrcImpl: GetScreenshotSrcFn = () => "";

// Register the functions from the context
export function registerBrowserFunctions({
  setUrl,
  setScreenshotSrc,
  getUrl,
  getScreenshotSrc,
}: {
  setUrl: SetUrlFn;
  setScreenshotSrc: SetScreenshotSrcFn;
  getUrl: GetUrlFn;
  getScreenshotSrc: GetScreenshotSrcFn;
}): void {
  setUrlImpl = setUrl;
  setScreenshotSrcImpl = setScreenshotSrc;
  getUrlImpl = getUrl;
  getScreenshotSrcImpl = getScreenshotSrc;
}

// Export the service functions
export const BrowserService = {
  setUrl: (url: string): void => {
    setUrlImpl(url);
  },

  setScreenshotSrc: (src: string): void => {
    setScreenshotSrcImpl(src);
  },

  getUrl: (): string => getUrlImpl(),

  getScreenshotSrc: (): string => getScreenshotSrcImpl(),
};

// Re-export the service functions for convenience
export const { setUrl, setScreenshotSrc, getUrl, getScreenshotSrc } =
  BrowserService;
