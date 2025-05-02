import { useDispatch } from "react-redux";
import { 
  initialState as browserInitialState,
  setUrl,
  setScreenshotSrc 
} from "#/state/browser-slice";

/**
 * Custom hook to reset browser state to initial values
 * 
 * This hook provides a function to reset the browser state to its initial values.
 * It's useful when navigating between conversations or when unmounting components
 * that use the browser state.
 */
export const useResetBrowserState = () => {
  const dispatch = useDispatch();

  /**
   * Reset browser state to initial values
   */
  const resetBrowserState = () => {
    dispatch(setUrl(browserInitialState.url));
    dispatch(setScreenshotSrc(browserInitialState.screenshotSrc));
  };

  return resetBrowserState;
};