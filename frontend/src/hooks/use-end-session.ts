import { useDispatch } from "react-redux";
import { useNavigate } from "react-router";
import {
  initialState as browserInitialState,
  setScreenshotSrc,
  setUrl,
} from "#/state/browser-slice";
import { clearSelectedRepository } from "#/state/initial-query-slice";
import { clearLastPage } from "#/utils/last-page";

export const useEndSession = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  /**
   * End the current session by clearing the token and redirecting to the home page.
   * @param {boolean} preserveLastPage - If true, don't clear the last page from localStorage
   */
  const endSession = (preserveLastPage = false) => {
    dispatch(clearSelectedRepository());

    // Reset browser state to initial values
    dispatch(setUrl(browserInitialState.url));
    dispatch(setScreenshotSrc(browserInitialState.screenshotSrc));

    // Check if the current page is a conversation page
    const isConversationPage = window.location.pathname.includes("/conversations/");
    
    // Clear the last page from localStorage unless preserveLastPage is true
    // or we're on a conversation page (to preserve the URL for after login)
    if (!preserveLastPage && !isConversationPage) {
      clearLastPage();
    }

    navigate("/");
  };

  return endSession;
};
