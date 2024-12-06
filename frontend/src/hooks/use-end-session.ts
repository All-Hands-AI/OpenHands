import { useDispatch } from "react-redux";
import { useNavigate } from "react-router";
import { useAuth } from "#/context/auth-context";
import {
  initialState as browserInitialState,
  setScreenshotSrc,
  setUrl,
} from "#/state/browser-slice";
import { clearSelectedRepository } from "#/state/initial-query-slice";

export const useEndSession = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { clearToken } = useAuth();

  /**
   * End the current session by clearing the token and redirecting to the home page.
   */
  const endSession = () => {
    clearToken();
    dispatch(clearSelectedRepository());

    // Reset browser state to initial values
    dispatch(setUrl(browserInitialState.url));
    dispatch(setScreenshotSrc(browserInitialState.screenshotSrc));

    navigate("/");
  };

  return endSession;
};
