import { OpenHandsAction } from "#/types/core/actions";
import { OpenHandsEventType } from "#/types/core/base";
import { isOpenHandsAction, isOpenHandsObservation } from "#/types/core/guards";
import { OpenHandsObservation } from "#/types/core/observations";

const COMMON_NO_RENDER_LIST: OpenHandsEventType[] = [
  "system",
  "agent_state_changed",
  "change_agent_state",
];

const ACTION_NO_RENDER_LIST: OpenHandsEventType[] = ["recall"];

export const shouldRenderEvent = (
  event: OpenHandsAction | OpenHandsObservation,
) => {
  if (isOpenHandsAction(event)) {
    const noRenderList = COMMON_NO_RENDER_LIST.concat(ACTION_NO_RENDER_LIST);
    return !noRenderList.includes(event.action);
  }

  if (isOpenHandsObservation(event)) {
    return !COMMON_NO_RENDER_LIST.includes(event.observation);
  }

  return true;
};
