import { setInitialized } from "#/state/taskSlice";
import store from "#/store";
import ActionType from "#/types/ActionType";
import { Settings } from "./settings";
import Socket from "./socket";

/**
 * Initialize the agent with the current settings.
 * @param settings - The new settings.
 */
export const initializeAgent = (settings: Settings) => {
  const event = { action: ActionType.INIT, args: settings };
  const eventString = JSON.stringify(event);

  store.dispatch(setInitialized(false));
  Socket.send(eventString);
};
