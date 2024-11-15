import store from "#/store";
import { initialState as browserInitialState } from "#/state/browserSlice";

/**
 * Clear the session data from the local storage and reset relevant Redux state
 */
export const clearSession = () => {
  // Clear local storage
  localStorage.removeItem("token");
  localStorage.removeItem("repo");

  // Reset browser state to initial values
  store.dispatch({
    type: "browser/setUrl",
    payload: browserInitialState.url,
  });
  store.dispatch({
    type: "browser/setScreenshotSrc",
    payload: browserInitialState.screenshotSrc,
  });
};
