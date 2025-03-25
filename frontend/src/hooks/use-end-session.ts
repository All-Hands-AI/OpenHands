import { useDispatch } from "react-redux";
import { useNavigate } from "react-router";
import { clearSelectedRepository } from "#/state/initial-query-slice";
import { DEFAULT_BROWSER_DATA, useBrowser } from "./state/use-browser";

export const useEndSession = () => {
  const { setScreenshotSrc, setUrl } = useBrowser();
  const navigate = useNavigate();
  const dispatch = useDispatch();

  /**
   * End the current session by clearing the token and redirecting to the home page.
   */
  const endSession = () => {
    dispatch(clearSelectedRepository());

    // Reset browser state to initial values
    setUrl(DEFAULT_BROWSER_DATA.url);
    setScreenshotSrc(DEFAULT_BROWSER_DATA.screenshotSrc);

    navigate("/");
  };

  return endSession;
};
