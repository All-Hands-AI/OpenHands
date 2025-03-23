import { useNavigate } from "react-router";
import { useInitialQuery } from "#/hooks/query/use-initial-query";
import { useBrowser } from "#/hooks/query/use-browser";

export const useEndSession = () => {
  const navigate = useNavigate();
  const { clearSelectedRepository } = useInitialQuery();
  const { setUrl, setScreenshotSrc } = useBrowser();

  /**
   * End the current session by clearing the token and redirecting to the home page.
   */
  const endSession = () => {
    clearSelectedRepository();

    // Reset browser state to initial values
    setUrl("https://github.com/All-Hands-AI/OpenHands");
    setScreenshotSrc("");

    navigate("/");
  };

  return endSession;
};
