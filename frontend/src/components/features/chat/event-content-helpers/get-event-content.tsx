import { Trans } from "react-i18next";
import { OpenHandsAction } from "#/types/core/actions";
import { isOpenHandsAction, isOpenHandsObservation } from "#/types/core/guards";
import { OpenHandsObservation } from "#/types/core/observations";
import { MonoComponent } from "../mono-component";
import { PathComponent } from "../path-component";
import { getActionContent } from "./get-action-content";
import { getObservationContent } from "./get-observation-content";
import i18n from "#/i18n";

const hasPathProperty = (
  obj: Record<string, unknown>,
): obj is { path: string } => typeof obj.path === "string";

const hasCommandProperty = (
  obj: Record<string, unknown>,
): obj is { command: string } => typeof obj.command === "string";

const trimText = (text: string, maxLength: number): string => {
  if (!text) return "";
  return text.length > maxLength ? `${text.substring(0, maxLength)}...` : text;
};

export const getEventContent = (
  event: OpenHandsAction | OpenHandsObservation,
) => {
  let title: React.ReactNode = "";
  let details: string = "";

  if (isOpenHandsAction(event)) {
    title = (
      <Trans
        i18nKey={`ACTION_MESSAGE$${event.action.toUpperCase()}`}
        values={{
          path: hasPathProperty(event.args) && event.args.path,
          command:
            hasCommandProperty(event.args) && trimText(event.args.command, 80),
        }}
        components={{
          path: <PathComponent />,
          cmd: <MonoComponent />,
        }}
      />
    );
    details = getActionContent(event);
  }

  if (isOpenHandsObservation(event)) {
    title = (
      <Trans
        i18nKey={`OBSERVATION_MESSAGE$${event.observation.toUpperCase()}`}
        values={{
          path: hasPathProperty(event.extras) && event.extras.path,
          command:
            hasCommandProperty(event.extras) &&
            trimText(event.extras.command, 80),
        }}
        components={{
          path: <PathComponent />,
          cmd: <MonoComponent />,
        }}
      />
    );
    details = getObservationContent(event);
  }

  return {
    title: title ?? i18n.t("EVENT$UNKNOWN_EVENT"),
    details: details ?? i18n.t("EVENT$UNKNOWN_EVENT"),
  };
};
