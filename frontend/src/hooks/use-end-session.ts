import { useNavigate } from "react-router";
import {
  setScreenshotSrc,
  setUrl,
} from "#/services/context-services/browser-service";

export const useEndSession = () => {
  const navigate = useNavigate();

  /**
   * End the current session by clearing the token and redirecting to the home page.
   */
  const endSession = () => {
    // Reset browser state to initial values
    setUrl("https://github.com/All-Hands-AI/OpenHands");
    setScreenshotSrc("");

    navigate("/");
  };

  return endSession;
};
